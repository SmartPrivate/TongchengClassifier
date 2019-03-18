from enum import Enum, unique


# 全局变量
@unique
class EmbeddingModelName(Enum):
    word2vec = 0
    bert = 1


min_prob: float = 50
