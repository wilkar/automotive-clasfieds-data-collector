import csv
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def get_score(file: str):
    with open(file, "r") as file:
        csv_reader = csv.DictReader(file)
        data: list = []
        labels: list = []

        for offer in csv_reader:
            description = offer["Description"]
            pattern = re.compile('<.*?>')

            clean_description = re.sub(pattern, '', description)
            data.append(clean_description)
            labels.append(offer["Suspicious"])

        vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
        X = vectorizer.fit_transform(data)
        y = labels
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        clf = LogisticRegression(max_iter=1000)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        print(classification_report(y_test, y_pred))
        print("Accuracy:", accuracy_score(y_test, y_pred))


get_score('balanced_set.csv')
