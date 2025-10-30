# Twitter Emotion Dataset Evaluation
Generated: 2025-10-17 05:08:33

## Dataset
- **Source**: `adhamelkomy/twitter-emotion-dataset` via kagglehub
- **Labels**: sadness (0), joy (1), love (2), anger (3), fear (4), surprise (5)
- **Total rows (after filtering)**: 416809
- **Sampled**: 0 rows per evaluation

## Models Evaluated
- **VADER**: Rule-based sentiment baseline (mapped to 6 emotions)
- **DistilRoBERTa-Emotion**: j-hartmann/emotion-english-distilroberta-base + RoBERTa sentiment
- **GoEmotions (Electra)**: google/electra-base-discriminator + RoBERTa sentiment
- **RoBERTa-Large (proxy)**: same analyzer interface, mapped outputs

## Summary Metrics
| Model | Accuracy | Avg Inference (s/text) | Samples |
|---|---:|---:|---:|
| VADER | 41.2% | 0.000 | 416809 |
| DistilRoBERTa-Emotion | 84.0% | 0.048 | 416809 |
| GoEmotions-Electra | 47.5% | 0.063 | 416809 |
| RoBERTa-Large | 84.0% | 0.049 | 416809 |

### VADER
#### Classification Report
| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| sadness | 0.475 | 0.448 | 0.461 | 121187 |
| joy | 0.502 | 0.818 | 0.623 | 141067 |
| love | 0.000 | 0.000 | 0.000 | 34554 |
| anger | 0.000 | 0.000 | 0.000 | 57317 |
| fear | 0.000 | 0.000 | 0.000 | 47712 |
| surprise | 0.030 | 0.147 | 0.050 | 14972 |

- Overall accuracy (sklearn): 0.412

#### Confusion Matrix (rows=true, cols=pred)
| true/pred | sadness | joy | love | anger | fear | surprise |
|---|---|---|---|---|---|---|
| sadness | 54246 | 42260 | 0 | 0 | 0 | 24681 |
| joy | 7656 | 115463 | 0 | 0 | 0 | 17948 |
| love | 3501 | 26045 | 0 | 0 | 0 | 5008 |
| anger | 25615 | 18307 | 0 | 0 | 0 | 13395 |
| fear | 20316 | 17922 | 0 | 0 | 0 | 9474 |
| surprise | 2918 | 9856 | 0 | 0 | 0 | 2198 |

### DistilRoBERTa-Emotion
#### Classification Report
| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| sadness | 0.893 | 0.915 | 0.904 | 121187 |
| joy | 0.821 | 0.926 | 0.871 | 141067 |
| love | 0.000 | 0.000 | 0.000 | 34554 |
| anger | 0.836 | 0.926 | 0.879 | 57317 |
| fear | 0.826 | 0.896 | 0.859 | 47712 |
| surprise | 0.696 | 0.852 | 0.766 | 14972 |

- Overall accuracy (sklearn): 0.840

#### Confusion Matrix (rows=true, cols=pred)
| true/pred | sadness | joy | love | anger | fear | surprise |
|---|---|---|---|---|---|---|
| sadness | 110862 | 2176 | 0 | 4620 | 3177 | 352 |
| joy | 5040 | 130696 | 0 | 1720 | 1541 | 2070 |
| love | 5618 | 24928 | 0 | 2493 | 1308 | 207 |
| anger | 1882 | 601 | 0 | 53047 | 1540 | 247 |
| fear | 617 | 219 | 0 | 1437 | 42744 | 2695 |
| surprise | 108 | 515 | 0 | 129 | 1460 | 12760 |

### GoEmotions-Electra
#### Classification Report
| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| sadness | 0.445 | 0.833 | 0.580 | 121187 |
| joy | 0.721 | 0.641 | 0.679 | 141067 |
| love | 0.000 | 0.000 | 0.000 | 34554 |
| anger | 0.105 | 0.118 | 0.111 | 57317 |
| fear | 0.000 | 0.000 | 0.000 | 47712 |
| surprise | 0.000 | 0.000 | 0.000 | 14972 |

- Overall accuracy (sklearn): 0.475

#### Confusion Matrix (rows=true, cols=pred)
| true/pred | sadness | joy | love | anger | fear | surprise |
|---|---|---|---|---|---|---|
| sadness | 100983 | 7692 | 0 | 12512 | 0 | 0 |
| joy | 27427 | 90388 | 0 | 23252 | 0 | 0 |
| love | 9943 | 16253 | 0 | 8358 | 0 | 0 |
| anger | 47596 | 2942 | 0 | 6779 | 0 | 0 |
| fear | 34523 | 3181 | 0 | 10008 | 0 | 0 |
| surprise | 6567 | 4827 | 0 | 3578 | 0 | 0 |

### RoBERTa-Large
#### Classification Report
| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| sadness | 0.893 | 0.915 | 0.904 | 121187 |
| joy | 0.821 | 0.926 | 0.871 | 141067 |
| love | 0.000 | 0.000 | 0.000 | 34554 |
| anger | 0.836 | 0.926 | 0.879 | 57317 |
| fear | 0.826 | 0.896 | 0.859 | 47712 |
| surprise | 0.696 | 0.852 | 0.766 | 14972 |

- Overall accuracy (sklearn): 0.840

#### Confusion Matrix (rows=true, cols=pred)
| true/pred | sadness | joy | love | anger | fear | surprise |
|---|---|---|---|---|---|---|
| sadness | 110862 | 2176 | 0 | 4620 | 3177 | 352 |
| joy | 5040 | 130696 | 0 | 1720 | 1541 | 2070 |
| love | 5618 | 24928 | 0 | 2493 | 1308 | 207 |
| anger | 1882 | 601 | 0 | 53047 | 1540 | 247 |
| fear | 617 | 219 | 0 | 1437 | 42744 | 2695 |
| surprise | 108 | 515 | 0 | 129 | 1460 | 12760 |

## Interpretation (Layperson)
- **What we measured**: How often each model correctly guessed the emotion for a tweet among six options.
- **Speed**: Time taken per tweet. Under ~0.2s is fine for real-time systems.
- **Why mappings**: Our pipeline predicts 10 emotions; this dataset has 6. We map similar emotions (e.g., positive→joy, trust→love).
- **How to read tables**: Accuracy shows overall wins; confusion matrices show where models confuse emotions (e.g., fear vs sadness).

## Recommendation
- **Best overall**: DistilRoBERTa-Emotion with accuracy 84.0% on the sampled Kaggle set.
- If accuracy and speed differ, prefer the model that balances both within your latency budget.
