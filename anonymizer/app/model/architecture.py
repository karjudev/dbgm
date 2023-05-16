import os
from pathlib import Path
from typing import List, Optional, Tuple
from torch import nn
from torch.nn.utils.rnn import pad_sequence
from lightning.pytorch import LightningModule
import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
from allennlp_light import ConditionalRandomField
from allennlp_light.modules.conditional_random_field.conditional_random_field import (
    allowed_transitions,
)
from app.model.encoding import ID2LABEL, LABEL2ID, encode_text, labels_to_spans

from app.schema import Span


class NERAnnotator(LightningModule):
    def __init__(
        self,
        encoder_model: str,
        lr: float = 1e-5,
        num_training_steps: int = 1,
        num_warmup_steps: int = 0,
        dropout_rate: float = 0.1,
        weight_decay: float = 0.01,
    ) -> None:
        super().__init__()
        self.encoder = AutoModel.from_pretrained(encoder_model, return_dict=True)
        self.__tokenizer = AutoTokenizer.from_pretrained(encoder_model)
        target_size = len(ID2LABEL)

        self.feedforward = nn.Linear(
            in_features=self.encoder.config.hidden_size, out_features=target_size
        )

        self.crf_layer = ConditionalRandomField(
            num_tags=target_size,
            constraints=allowed_transitions(constraint_type="BIO", labels=ID2LABEL),
        )

        self.dropout = nn.Dropout(dropout_rate)

        self.save_hyperparameters()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """Forward pass of the neural network.

        Args:
            input_ids (torch.Tensor): Input IDs encoding of the text.
            attention_mask (torch.Tensor): Attention mask.

        Returns:
            Tuple[torch.Tensor, Optional[torch.Tensor]]: Predicted label and possible loss.
        """
        batch_size = input_ids.size(0)

        embedded_text_input = self.encoder(
            input_ids=input_ids, attention_mask=attention_mask
        )
        embedded_text_input = embedded_text_input.last_hidden_state
        embedded_text_input = self.dropout(F.leaky_relu(embedded_text_input))

        # project the token representation for classification
        token_scores = self.feedforward(embedded_text_input)
        token_scores = F.log_softmax(token_scores, dim=-1)

        # Computes the list of predicted labels
        best_path = self.crf_layer.viterbi_tags(token_scores, attention_mask)
        # Produces the tensor of predicted labels
        pred_results = [
            torch.tensor(label_seq, dtype=torch.int) for label_seq, _ in best_path
        ]
        pred_labels = pad_sequence(
            pred_results, batch_first=True, padding_value=LABEL2ID["O"]
        )

        # If the labels are specified, computes the loss
        loss = None
        if labels is not None:
            loss = -self.crf_layer(token_scores, labels, attention_mask) / float(
                batch_size
            )
        return pred_labels, loss

    def predict(self, text: str) -> List[Span]:
        """Predicts a list of spans for a text.

        Args:
            text (str): Text to predict.

        Returns:
            List[Span]: List of spans.
        """
        # Encodes the text
        input_ids, attention_mask, offset_mapping = encode_text(text, self.__tokenizer)
        # Computes the labels and discards the None loss
        with torch.no_grad():
            label_ids, _ = self(input_ids, attention_mask)
        # Converts the labels to spans
        spans = []
        for labels, offsets in zip(label_ids, offset_mapping):
            span = labels_to_spans(labels, offsets)
            spans.extend(span)
        return spans

    @classmethod
    def from_directory(cls, directory: Path) -> "NERAnnotator":
        """Loads the NER annotator from disk.

        Args:
            directory (Path): Directory where the model is stored.

        Returns:
            NERAnnotator: NER annotation model.
        """
        # File where the hyperparameters are stored
        hparams_file = directory / "hparams.yaml"
        assert hparams_file.is_file()
        # Checkpoint of the model
        checkpoint = Path(
            [
                entry
                for entry in os.scandir(directory / "checkpoints")
                if entry.path.endswith("final.ckpt")
            ][0]
        )
        # Loads the model from disk
        model = NERAnnotator.load_from_checkpoint(
            checkpoint_path=checkpoint, hparams_file=hparams_file
        )
        return model
