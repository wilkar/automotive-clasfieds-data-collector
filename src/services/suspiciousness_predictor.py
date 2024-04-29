from joblib import load  # type: ignore
from enum import StrEnum
from src.services.helpers.data_normalizer import clean_text
import numpy as np


class mode(StrEnum):
    vin = "vin"
    manual = "description"


class ml_model(StrEnum):
    logistic_regression = "LogisticRegression"
    random_forest_classifier = "RandomForestClassifier"
    gradient_boosting_classifier = "GradientBoostingClassifier"
    ada_boost_classifier = "AdaBoostClassifier"
    extra_tree_classifier = "ExtraTreesClassifier"
    k_neighbors_classifier = "KNeighborsClassifier"


class SuspiciousnessPredictor:
    def __init__(self, offer: dict, ml_model: ml_model, mode: mode):
        self.offer = offer
        self.ml_model = ml_model
        self.mode = mode

    def predict_suspiciousness(self) -> dict:
        text_input = f'{self.offer.get("title", "")} {self.offer.get("description", "")} {str(self.offer.get("price", ""))} {str(self.offer.get("milage", ""))} {self.offer.get("model", "")} {self.offer.get("condition", "")} {self.offer.get("country_origin", "")} {self.offer.get("vin", "")}'
        model_path = f"ml_models/{self.ml_model.value}_{self.mode.value}.joblib"
        model_pipeline = load(model_path)
        input_data = clean_text(text_input)

        proba = model_pipeline.predict_proba([input_data])[0][1]

        return proba
