import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    average_precision_score,  # type: ignore
    confusion_matrix,
    precision_recall_curve,
)


def plot_confusion_matrix(y_true, y_pred, model_name, mode):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 7))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Not Suspicious", "Suspicious"],
        yticklabels=["Not Suspicious", "Suspicious"],
    )
    plt.xlabel("Predicted labels")
    plt.ylabel("True labels")
    plt.title(f"Confusion Matrix for {model_name} with training data from {mode}")
    plt.savefig(f"plots/confusion_matrix_{model_name}-{mode}.png")
    plt.close()


def plot_precision_recall_curve(model_name, y_true, y_scores, mode):
    precision, recall, _ = precision_recall_curve(y_true, y_scores)
    average_precision = average_precision_score(y_true, y_scores)

    plt.figure()
    plt.step(
        recall,
        precision,
        where="post",
        color="b",
        alpha=0.2,
        label=f"Average precision = {average_precision:0.2f}",
    )
    plt.fill_between(recall, precision, step="post", alpha=0.2, color="b")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.ylim([0.0, 1.05])
    plt.xlim([0.0, 1.0])
    plt.title(f"Precision-Recall Curve using training data from {mode}")
    plt.legend(loc="upper right")
    plt.savefig(f"plots/precision_recall_curve_{model_name}-{mode}.png")
    plt.close()
