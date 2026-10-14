"""Small local-file ONNX encoder; never download weights on a query request."""

from pathlib import Path


class OnnxEncoder:
    def __init__(self, tokenizer_path: Path, model_path: Path):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(str(model_path), sess_options=options, providers=["CPUExecutionProvider"])

    def encode(self, texts: list[str]):
        import numpy as np

        if not 1 <= len(texts) <= 16 or any(len(text) > 16000 for text in texts):
            raise ValueError("Encoder requires 1–16 bounded text inputs")
        tokens = self.tokenizer.encode_batch(texts)
        inputs = {
            "input_ids": np.array([item.ids for item in tokens], dtype=np.int64),
            "attention_mask": np.array([item.attention_mask for item in tokens], dtype=np.int64),
            "token_type_ids": np.array([item.type_ids for item in tokens], dtype=np.int64),
        }
        inputs = {item.name: inputs[item.name] for item in self.session.get_inputs()}
        hidden = self.session.run(None, inputs)[0]
        return normalized_mean_pool(hidden, inputs["attention_mask"])


def normalized_mean_pool(hidden, attention_mask):
    import numpy as np

    mask = attention_mask[:, :, None].astype(np.float32)
    pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1e-9)
    vectors = pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-9)
    if not np.isfinite(vectors).all() or vectors.shape[-1] != 384:
        raise ValueError("Invalid model embedding representation")
    return vectors
