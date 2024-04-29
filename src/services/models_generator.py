import asyncio
import datetime
import logging
from enum import StrEnum

import pandas as pd
from joblib import dump  # type: ignore
from pandas import Series
from sklearn.ensemble import (
    AdaBoostClassifier,  # type: ignore
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from sklearn.linear_model import LogisticRegression  # type: ignore
from sklearn.metrics import (
    accuracy_score,
    f1_score,  # type: ignore
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split  # type: ignore
from sklearn.neighbors import KNeighborsClassifier  # type: ignore
from sklearn.pipeline import make_pipeline  # type: ignore

from src.config import log_init
from src.services.dataset_generator import DataSetBuilder
from src.services.helpers.data_normalizer import clean_text
from src.services.model_visualization import (
    plot_confusion_matrix,
    plot_precision_recall_curve,
)

log_init.setup_logging()

logger = logging.getLogger(__name__)

models = {
    "LogisticRegression": LogisticRegression(),
    "RandomForestClassifier": RandomForestClassifier(),
    "GradientBoostingClassifier": GradientBoostingClassifier(),
    "AdaBoostClassifier": AdaBoostClassifier(),
    "ExtraTreesClassifier": ExtraTreesClassifier(),
    "KNeighborsClassifier": KNeighborsClassifier(),
}


class mode(StrEnum):
    vin = "vin"
    manual = "description"


class ModelsGenerator:
    def __init__(self, models: dict[str, object]):
        self.models = models
        self.dataset_generator = DataSetBuilder()

    async def evaluate_models_with_manually_labeled_offers(self):
        dataset = (
            await self.dataset_generator._prepare_dataset_with_manually_labeled_offers()
        )
        X_train, X_test, y_train, y_test = await self._build_model(dataset)

        evaluation_results = {}

        for model_name, model in self.models.items():
            logger.info(f"Evaluating model {model} in {mode.manual.value}")
            await self._evaluate_model(
                model_name, model, X_train, y_train, X_test, y_test, mode.manual.value
            )

        return evaluation_results

    async def evaluate_models_with_suspicious_vin_numbers(self):
        dataset = (
            await self.dataset_generator._prepare_dataset_with_suspicious_vin_numbers()
        )
        X_train, X_test, y_train, y_test = await self._build_model(dataset)

        evaluation_results = {}

        for model_name, model in self.models.items():
            logger.info(f"Evaluating model {model} in {mode.manual.value}")
            await self._evaluate_model(
                model_name, model, X_train, y_train, X_test, y_test, mode.vin.value
            )

        return evaluation_results

    async def _evaluate_model(
        self,
        model_name: str,
        model: object,
        X_train: Series,
        y_train: Series,
        X_test: Series,
        y_test: Series,
        mode: str,
    ):
        evaluation_results: dict = {}
        start_time = datetime.datetime.now()

        pipeline = make_pipeline(TfidfVectorizer(), model)
        pipeline.fit(X_train, y_train)

        await self._save_model(pipeline, model_name, mode)

        y_pred = pipeline.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        end_time = datetime.datetime.now()
        duration = end_time - start_time

        y_pred = pipeline.predict(X_test)
        logger.info(f"Saving model visualization {model} in {mode}")
        if hasattr(model, "predict_proba"):
            y_scores = pipeline.predict_proba(X_test)[:, 1]
            plot_precision_recall_curve(
                model_name,
                y_test,
                y_scores,
                mode,
            )
            plot_confusion_matrix(y_test, y_pred, model_name, mode)

        evaluation_results[model_name] = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1-score": f1,
            "start_time": start_time,
            "end_time": end_time,
            "build_time_seconds": duration.seconds,
        }
        logger.info(f"Model summary for {model} in {mode}: {evaluation_results}")
        return evaluation_results

    async def _build_model(
        self, dataset: list
    ) -> tuple[Series, Series, Series, Series]:
        logger.info(f"Preparing dataset")
        df = pd.DataFrame(dataset)

        df["text"] = (
            df["title"].fillna("")
            + " "
            + df["description"].fillna("")
            + " "
            + df["price"].astype(str)
            + " "
            + df["milage"].astype(str)
            + " "
            + df["model"].fillna("")
            + " "
            + df["condition"].fillna("")
            + " "
            + df["country_origin"].fillna("")
            + " "
            + df["vin"].fillna("")
        )

        df["cleaned_text"] = df["text"].apply(clean_text)

        X = df["cleaned_text"]
        y = df["is_suspicious"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        return X_train, X_test, y_train, y_test

    async def _save_model(self, model_pipeline, model_name, mode):
        model_path = f"ml_models/{model_name}_{mode}.joblib"
        dump(model_pipeline, model_path)
        logger.info(f"Saving model")
        return model_path


if __name__ == "__main__":
    test = ModelsGenerator(models)
    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(test.evaluate_models_with_manually_labeled_offers()),
        loop.create_task(test.evaluate_models_with_suspicious_vin_numbers()),
    ]
    results = loop.run_until_complete(asyncio.gather(*tasks))

    for result in results:
        print(result)
