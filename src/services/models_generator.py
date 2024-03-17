import asyncio
import datetime

import pandas as pd
from joblib import dump, load
from pandas import DataFrame
from sklearn.ensemble import (AdaBoostClassifier, ExtraTreesClassifier,
                              GradientBoostingClassifier,
                              RandomForestClassifier)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline

from src.repositories.helpers import get_engine
from src.repositories.offer.sql_alchemy import SqlAlchemyOfferRepository
from src.services.data_normalizer import clean_text
from src.services.model_visualization import (plot_confusion_matrix,
                                              plot_precision_recall_curve)

models = {
    "LogisticRegression": LogisticRegression(),
    "RandomForestClassifier": RandomForestClassifier(),
    "GradientBoostingClassifier": GradientBoostingClassifier(),
    "AdaBoostClassifier": AdaBoostClassifier(),
    "ExtraTreesClassifier": ExtraTreesClassifier(),
    "KNeighborsClassifier": KNeighborsClassifier(),
}


async def _save_cleaned_data(dataset: DataFrame, filename="cleaned_data.csv"):
    dataset.to_csv(filename, sep=",", index=True, encoding="utf-8")


async def _prepare_dataset():
    engine = get_engine()
    scraped_offer_repository = SqlAlchemyOfferRepository(engine)
    all_offers = await scraped_offer_repository.select_all_offers()
    all_suspicious = await scraped_offer_repository.select_all_suspicious_offers()
    suspicious_dict = {
        offer.suspicious_clasfieds_id: offer.is_suspicious for offer in all_suspicious
    }

    dataset = []
    for offer in all_offers:
        is_suspicious = suspicious_dict.get(offer.clasfieds_id, False)
        dataset.append(
            {
                "title": offer[1],
                "description": offer[2],
                "model": offer[3],
                "price": offer[4],
                "milage": offer[5],
                "condition": offer[6],
                "country_origin": offer[7],
                "is_suspicious": is_suspicious,
            }
        )

    return dataset


async def _build_model(dataset: list):
    df = pd.read_csv("cleaned_data.csv")

    # df["text"] = (
    #     df["title"].fillna("")
    #     + " "
    #     + df["description"].fillna("")
    #     + " "
    #     + df["price"].astype(str)
    #     + " "
    #     + df["milage"].astype(str)
    #     + " "
    #     + df["model"].fillna("")
    #     + " "
    #     + df["condition"].fillna("")
    #     + " "
    #     + df["country_origin"].fillna("")
    # )

    # df["cleaned_text"] = df["text"].swifter.apply(clean_text)

    # Split the data into features and target labels
    X = df["cleaned_text"]
    y = df["is_suspicious"]
    await _save_cleaned_data(df)

    # Split data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Note: At this point, X_train and X_test are still in textual form and need to be vectorized.
    return X_train, X_test, y_train, y_test


async def _save_model(model_pipeline, model_name):
    model_path = f"ml_models/{model_name}.joblib"
    dump(model_pipeline, model_path)
    return model_path


async def evaluate_models(models):
    # Load and prepare your dataset
    dataset = await _prepare_dataset()
    X_train, X_test, y_train, y_test = await _build_model(dataset)

    evaluation_results = {}

    for model_name, model in models.items():
        start_time = datetime.datetime.now()
        # Integrate TfidfVectorizer into your model pipeline
        pipeline = make_pipeline(TfidfVectorizer(), model)
        pipeline.fit(X_train, y_train)

        # Save the entire pipeline, including the vectorizer
        await _save_model(pipeline, model_name)

        # Evaluate the model
        y_pred = pipeline.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        end_time = datetime.datetime.now()
        duration = end_time - start_time

        evaluation_results[model_name] = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1-score": f1,
            "build_time_seconds": duration.seconds,
        }
        ####

        # Your model training and evaluation logic

        # After model evaluation, directly call your plotting functions
        # Example for plot_confusion_matrix:
        y_pred = pipeline.predict(
            X_test
        )  # Ensure model is your trained model pipeline including vectorization

        # Ensure you're using the correct data for other visualizations
        # For plot_precision_recall_curve, you need y_scores from predict_proba or decision_function
        if hasattr(model, "predict_proba"):
            y_scores = pipeline.predict_proba(X_test)[:, 1]
            plot_precision_recall_curve(
                model_name, y_test, y_scores, f"Precision-Recall Curve for {model_name}"
            )
            plot_confusion_matrix(y_test, y_pred, model_name)

        ####
        print(f"{model_name} accuracy: {accuracy}")
        print(f"{model_name} precision: {precision}")
        print(f"{model_name} recall: {recall}")
        print(f"{model_name} F1-score: {f1}")
        print(f"{model_name} build time: {duration.seconds} seconds")

    return evaluation_results


async def predict_suspiciousness(
    offer_id: int,
    title: str,
    description: str,
    price: int,
    milage: int,
    model: str,
    condition: str,
    country_origin: str,
) -> dict:
    model_names = [
        "LogisticRegression",
        "RandomForestClassifier",
        "GradientBoostingClassifier",
        "AdaBoostClassifier",
        "ExtraTreesClassifier",
        "KNeighborsClassifier",
    ]

    text_input = (
        f"{title} {description} {price} {milage} {model} {condition} {country_origin}"
    )

    predictions = {}

    for model_name in model_names:
        model_pipeline = load(f"ml_models/{model_name}.joblib")

        if hasattr(model_pipeline, "predict_proba"):
            proba = model_pipeline.predict_proba([text_input])[0][1]
        else:
            decision_function = model_pipeline.decision_function([text_input])
            proba = decision_function[0]

        predictions[model_name] = proba
    print(f"'Prediction for offer_id {offer_id}': {predictions}")
    return predictions


list_of_offers = [
    {
        "clasfieds_id": 904477333,
        "title": "Citroën DS5",
        "description": "Sprzedam Citroena DS5 wersja hybrid. Pakiet sochip. Opony letnie na felgach aluminiowych,zima na białych. Ostatnio wymienione tarcze i klocki Olej i filtry wymieniane systematycznie co rok. Jeździmy nim 5 lat Polecam. W sprawie samochodu proszę dzwonić. Nie odpowiadam na maile i smsy.",
        "price": 41000,
        "milage": 163000,
        "model": "Pozostałe Citroen",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 888472009,
        "title": "Hyundai Kona N Line! Hybrid! Asystenci! Kamera! Apple CarPlay!",
        "description": "Hyundai Kona N-Line Hybrid!  <br /> <br /> Opis pojazdu<br /> <br /> Rok produkcji 2022, pierwsza rejestracja 29.04.2022 r.<br /> Silnik benzynowy + hybryda o pojemności 1.0 i mocy 120 KM.<br /> Skrzynia biegów manualna, sześciostopniowa.<br /> Przebieg 23990 km, pisemna gwarancja przebiegu!<br /> <br /> Bardzo czysty i zadbany, bez wkładu finansowego.<br /> Opony letnie z roku 2022, rozmiar 235/45R18.<br /> <br /> Wykonany świeży serwis w ASO Hyundai!<br /> Na gwarancji fabrycznej!<br /> Zarejestrowany i ubezpieczony w Polsce.<br /> Samochodem można wracać do domu na kołach.<br /> <br /> W celu potwierdzenia aktualności oferty prosimy o telefon przed przyjazdem.<br /> <br /> Zapraszamy do bezpłatnej jazdy testowej, która umożliwi Państwu ocenę rzeczywistego stanu pojazdu.<br /> <br /> *Możliwy transport do klienta.<br /> <br /> Gwarancja<br /> <br /> Każdy samochód dostępny w naszej ofercie jest szczegółowo sprawdzony przez nasz wykwalifikowany personel a także posiada pozytywne wyniki badania technicznego przeprowadzonego w Polsce. <br /> <br /> Wszystkie ewentualne usterki są naprawiane a Klient na wykonana naprawę otrzymuje pisemną gwarancję.<br /> <br /> Za dodatkową opłatą istnieje możliwość wykupienia gwarancji na samochód u jednego z naszych partnerów. <br /> <br /> Formy płatności:<br /> <br /> •\tgotówka,<br /> •\tprzelew bankowy,<br /> •\tsprzedaż ratalna,<br /> •\tleasing,<br /> •\tmożliwość pozostawienia samochodu w rozliczeniu.<br /> <br /> W przypadku zainteresowania ofertą kredytu lub leasingu prosimy o kontakt z naszym Specjalistą do spraw Finansowania Samochodów - Panią Aleksandrą Dziedzic tel.:  <br /> <br /> Dla Klientów OLX więcej zdjęć na stronie OTOMOTO.<br /> <br /> Godziny otwarcia salonu:<br /> <br /> •\tod poniedziałku do piątku 9:00 – 17:00<br /> •\tsoboty 9:00 – 15:00<br /> <br /> Możliwość otwarcia Salonu w niedzielę lub poza godzinami pracy tylko po wcześniejszych ustaleniach telefonicznych. <br /> <br /> Ogłoszenie ma charakter informacyjny i stanowi zaproszenie do zawarcia umowy (art. 71 Kodeksu cywilnego); nie stanowi natomiast oferty handlowej w rozumieniu art. 66 § 1 Kodeksu cywilnego. W celu sprawdzenia zgodności oferty oraz uzyskania wszelkich informacji prosimy o kontakt. Przedstawione zdjęcia są poglądowe.",
        "price": 79900,
        "milage": 23990,
        "model": "Kona",
        "condition": "Nieuszkodzony",
        "country_origin": "Hiszpania",
    },
    {
        "clasfieds_id": 812355233,
        "title": "Honda Civic TypeR GT 310KM",
        "description": "Honda Civic TypeR silnik 2.0T i VTEC o mocy 310 KM, manualna skrzynia biegów,<br /> <br /> wersja wyposażenia GT<br /> <br /> Auto w stanie bardzo dobrym, doposażony, nie wymaga wkładu finansowego.<br /> <br /> KONTAKT:<br />  ARTUR<br /> <br /> AUTORYZOWANY DEALER HONDA WYSZOMIRSKI W SIEDLCACH<br /> <br /> Informacje umieszczone na stronie internetowej służą jedynie celom informacyjnym i nie stanowią oferty w rozumieniu przepisów Kodeksu Cywilnego oraz opisu towaru ani zapewnienia w rozumieniu art. 4 Ustawy z dnia 27 lipca 2002 roku o szczególnych warunkach sprzedaży konsumenckiej.<br /> <br /> Indywidualne uzgodnienie właściwości i specyfikacji pojazdu następuje w umowie sprzedaży.",
        "price": 109900,
        "milage": 67800,
        "model": "Civic",
        "condition": "Nieuszkodzony",
        "country_origin": "Niemcy",
    },
    {
        "clasfieds_id": 888316270,
        "title": "Mercedes-Benz GLE GLE 350 de AMG 63 4MATIC faktura Vat23%",
        "description": "Dzień dobry ,<br /> <br /> W ofercie do sprzedania samochód Mercedes Gle w167 Plug in diesel - hybryda 320/KM.<br /> Właściciel niepalący.<br /> Moc samochodu jest stała 320 /KM niezależne od tego czy bateria jest rozładowana .<br /> <br /> Cena w ogłoszeniu jest ceną brutto już z VAT 23% <br /> Wystawiam  fakturę VAT 23% <br /> Osoba kupującą zwolniona z podatku 2% .<br /> <br /> Zapraszam do kontaktu telefonicznego<br /> <br /> Tempomat<br /> Lampy przednie w technologii LED<br /> Kontrola odległości z przodu (przy parkowaniu)<br /> Kontrola odległości z tyłu (przy parkowaniu)<br /> Park Assistant - asystent parkowania<br /> Niezależny system parkowania<br /> Kamera panoramiczna 360<br /> Kamera parkowania tył<br /> Lusterka boczne ustawiane elektrycznie<br /> Podgrzewane lusterka boczne<br /> Lusterka boczne składane elektrycznie<br /> Asystent (czujnik) martwego pola<br /> Aktywny asystent zmiany pasa ruchu<br /> Lane assist - kontrola zmiany pasa ruchu<br /> Ogranicznik prędkości<br /> Asystent hamowania - Brake Assist<br /> Kontrola trakcji<br /> Wspomaganie ruszania pod górę- Hill Holder<br /> System rozpoznawania znaków drogowych<br /> Asystent świateł drogowych<br /> Oświetlenie adaptacyjne<br /> Dynamiczne światła doświetlające zakręty<br /> Czujnik zmierzchu<br /> Lampy doświetlające zakręt<br /> Światła do jazdy dziennej<br /> Światła do jazdy dziennej diodowe LED<br /> Lampy tylne w technologii LED<br /> Oświetlenie drogi do domu<br /> Oświetlenie wnętrza LED<br /> System Start/Stop<br /> Elektroniczna kontrola ciśnienia w oponach<br /> Elektryczny hamulec postojowy<br /> Wspomaganie kierownicy<br /> <br /> Audio i multimedia:<br /> <br /> Apple CarPlay<br /> Android Auto<br /> Interfejs Bluetooth<br /> Radio<br /> Zestaw głośnomówiący<br /> Gniazdo USB<br /> Ładowanie bezprzewodowe urządzeń<br /> System nawigacji satelitarnej<br /> System nagłośnienia<br /> Ekran dotykowy<br /> Sterowanie funkcjami pojazdu za pomocą głosu<br /> Dostęp do internetu<br /> <br /> Bezpieczeństwo:<br /> <br /> ABS<br /> ESP<br /> Elektroniczny system rozdziału siły hamowania<br /> System wspomagania hamowania<br /> System ostrzegający o możliwej kolizji<br /> System wykrywania zmęczenie kierowcy<br /> Asystent pasa ruchu<br /> System powiadamiania o wypadku<br /> Poduszka powietrzna kierowcy<br /> Poduszka powietrzna pasażera<br /> Poduszka kolan kierowcy<br /> Kurtyny powietrzne - przód<br /> Boczna poduszka powietrzna kierowcy<br /> Boczne poduszki powietrzne - przód<br /> Kurtyny powietrzne - tył<br /> Isofix (punkty mocowania fotelika dziecięcego)",
        "price": 315000,
        "milage": 37000,
        "model": "Pozostałe Mercedes",
        "condition": "Nieuszkodzony",
        "country_origin": "Niemcy",
    },
    {
        "clasfieds_id": 890772777,
        "title": "Nissan Qashqai Jak nowy stan idealny",
        "description": "Witam sprzedam  NISSAN QASHQAI z silnikiem benzynowym 1.3 158KM w bardzo bogatej wersji:<br /> Pierwsza rej 25. 11 .2021 r<br /> Automatyczna skrzynia biegów<br /> ● Podgrzewana przednia szyba<br /> ● Podgrzewana kierownica<br /> ● Kamera cofania<br /> ● System wspomagania ruszania pod górę - USS<br /> ● Wyświetlacz TFT 5” zintegrowany z zestawem wskaźników<br /> ● Światła do jazdy dziennej LED<br /> ● Tempomat z ogranicznikiem prędkości<br /> ● System Start/Stop<br /> ● Przednie i tylne szyby elektryczne<br /> ● 17” koła ze stopu metali lekkich<br /> ● Dwustrefowa automatyczna klimatyzacja<br /> ● Automatyczne wycieraczki i czujnik deszczu<br /> ● System audio z 6 głośnikami<br /> ● Regulacja wysokości fotela kierowcy i pasażera<br /> ● Miękka skóra na kierownicy oraz gałce dźwigni zmiany biegów<br /> I napewno jeszcze by sie coś znalazło <br /> Samochód został sprowadzony z Danii w czerwcu zeszłego roku. <br /> Samochód bezwypadkowy <br /> Samochód serwisowany na bieżąco, w bardzo dobrym stanie technicznym<br /> Nowe opony zima, ostatnio wymienione klocki przód tył w grudniu wymieniony olej i wszystkie filtry<br /> Autko można sprawdzić na każdej stacji<br /> Autko użytkuje prywatnie ale czas zmienić na coś nowszego. <br /> Na samochód wystawiany fakturę VAT.<br /> Cena netto 90 000 tyś bez negocjacji !!! <br /> Kontakt",
        "price": 111930,
        "milage": 42300,
        "model": "Qashqai",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 838380606,
        "title": "Nissan Qashqai Nissan Qashqai 1.2 BENZYNA opony lato/zima, kamery 360,super stan",
        "description": 'Auto zarejestrowane w pięknym kolorze biała perła, serwisowane   i ubezpieczone w Polsce,  niski przebieg tylko 118 tys. km 2 kluczyki , dwa komplety opon lato/zima, nowy akumulator BOSCH  z 2 letnią gwarancją <br /> bogata wersja wyposażenia <br /> KAMERY 360<br /> System Keyless Go<br /> Nawigacja <br /> ABS + EBD<br /> Inteligentny system wspomagania hamowania<br /> ESP<br /> RADAR<br /> asystent pasa ruchu <br /> tempomat<br /> limiter prędkości<br /> rozpoznawanie znaków<br /> podgrzewane fotele <br /> automatyczna zmiana świateł mijania/drogowe<br /> System wspomagania ruszania pod górę z funkcja Auto Hold<br /> Automatyczne wycieraczki i czujnik deszczu<br /> Elektryczny hamulec postojowy<br /> System pomiaru ciśnienia w oponach<br /> System audio z radiem/CD, MP3, AUX, USB i iPod, Bluetooth<br /> 6 głośniki<br /> Wyświetlacz TFT 5” zintegrowany z zestawem wskaźników<br /> Światła do jazdy dziennej w technologii LED<br /> Tylne światła w technologii LED<br /> Wszystkie szyby elektryczne <br /> Kolumna kierownicy z regulacją w dwóch płaszczyznach<br /> System Start/Stop<br /> Lusterka zewnętrzne regulowane i podgrzewane elektrycznie ze zintegrowanymi kierunkowskazami LED<br /> Miękką skórę na kierownicy oraz gałce dźwigni zmiany biegów<br /> Podświetlaną obwódkę gałki zmiany biegów<br /> 17" felgi ze stopów metali lekkich<br /> Przednie lampy przeciwmgłowe<br /> Ręcznie regulowane podparcie odcinka lędźwiowego w fotelu kierowcy i pasażera<br /> Automatycznie składane lusterka<br /> kontakt',
        "price": 73900,
        "milage": 118000,
        "model": "Qashqai",
        "condition": "Nieuszkodzony",
        "country_origin": "Finlandia",
    },
    {
        "clasfieds_id": 899523001,
        "title": "Opel Astra Opel Astra Sports Tourer Dynamic 1.4 150 AT6",
        "description": "Opel Astra Sports Tourer Dynamic 1.4 150 AT6 <br /> Felgi 18 cali z rocznymi oponami wielosezonowymi <br /> Adaptacyjny tempomat<br /> Podgrzewana kierownica oraz fotele<br /> Fotele przednie z elektryczna regulacją<br /> Reflektory Intellilux<br /> Dostęp bez kluczykowy<br /> Hak holowniczy<br /> Samochód garażowany <br /> Automatyczna skrzynia biegów<br /> Więcej informacji udzielę telefonicznie<br /> Osoby z OLX zapraszam na OtoMoto, jest tam więcej zdjęć.",
        "price": 47000,
        "milage": 142000,
        "model": "Astra",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 887991390,
        "title": "Lexus NX Lexus nx200t",
        "description": "Samochód w bardzo dobrym stanie.<br /> Posiadamy go od 2018 roku.<br /> Stan samochodu był sprawdzany w polskim salonie LEXUSA<br /> Lexus NX 200T 2.0 benzyna<br /> AUTOMAT ,ABS, ESP 7x Airbag Tempomat<br /> AUTO HOLD, Czujnik deszczu, Czujnik zmierzchu<br /> Elektryczne szyby x4, Reflektory ksenonowe<br /> Klimatronik dwustrefowy, Światła do jazdy dziennej LED<br /> Fabryczny zestaw głośnomówiący Bluetooth<br /> Skórzana, wielofunkcyjna kierownica<br /> Fotochromatyczne lusterko wsteczne<br /> Elektryczne lusterka<br /> Centralny zamek z pilotem<br /> skórzana tapicerka<br /> Aluminiowe felgi ”17” Czujniki ciśnienia opon<br /> Podgrzewane fotele, wentylowane fotele<br /> Kamera cofania, Immobilizer, alarm<br /> Halogeny<br /> Radio CD<br /> Isofix<br /> 2 kluczyki<br /> Sterowanie głosowe<br /> System Inteligentny kluczyk, z klamkami zewnętrznymi podświetlanymi<br /> LED<br /> Wejście USB i AUX dla zewnętrznych urządzeń audio<br /> Interfejs Remote Touch Pad do obsługi multimediów",
        "price": 102000,
        "milage": 32000,
        "model": "Pozostałe Lexus",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 887809660,
        "title": "Hyundai i10 New! i10 1.0Mpi 67KM BogatoWypos Gwar.Producenta! bezwypadkowy 1lakier",
        "description": "Do sprzedaży wystawiono tyle co przywiezionego z za granicy z prywatnego użytku - po opłatach pełnej akcyzy za pojazd nie uszkodzony (czysty cepik) będący z dnia na dzień zarejestrowany i ubezpieczony w Polsce - w stanie jak tu na fotos oferty ,sprawnego z pierwszym lakierem po pierwszej prywatnej, niepalącej właścicielce po 50-tce - bezwypadkowego ,garażowanego ,czystego i kompletnego niczym w stanie jak ,,nowy'' z przebiegiem ponad 10tyś.km - na gwarancji producenta w najnowszym wydaniu tego modelu ,bdb wyposażony ,komfortowy ,pojemny ,bezawaryjny i ekonomiczny wykonany w niezawodnej technologii na lata udanej jazdy ,w ładnym malowaniu nadwozia w kolorze ciemny-popiel metalik   w stanie wsiadasz/jedziesz ,niczym nówka polecany najnowszy model HYUNDAI i10 Pure Edition 1,0Mpi 67KM z niezawodnym benzynowym silnikiem - trwałym i bezawaryjnym ,dzięki swej prostocie na długie lata bezproblemowej jazdy ,nie uturbionym benzynowym bezstresowym w eksploatacji ,która na ogół ogranicza się do wymiany oleju silnika i filtrów co 15tys.km i nic nad to! Rozrząd jest na ogół do żywotni - spięty trwałym łańcuchem rozrządu ,który przy wersji bez turbo-doładowania nie jest podatny na wyciąganie się i nie podlega najczęściej potrzebie wymiany. Silnik ten będąc połączony z precyzyjnie pracującą manualną skrzynią biegów ,z wydajnym układem hamulcowym i świetnie zestrojonym zawieszeniem w dość lekkim nadwoziu i10 sprawia ,że jazda nim jest pełna pozytywnych wrażeń ,a bdb wyposażenie wewnątrz oraz liczni asystencji wspomagania jazdy ,kontroli prowadzenia i wysoko punktowany poziom bezpieczeństwa sprawia ,że chętnie się do niego wraca do woli ujeżdżając przy jakże niskim spalaniu ,które w mieście kształtuje się w granicach do max.5,0 litr./100km ,a w trasie od 3,6-4,4 litr./100km w zależności od stylu jazdy ,obciążenia i prędkości przejazdowej! V-max pokazanego tu i10 to ok.175km/h przy czym prowadzi się bez żadnych negatywnych uwag! Patrząc nań jak na miejskie auto wygodnego miejsca i komfortu w podróży nie zabraknie ,a sam bagażnik mimo słusznego gabarytu tego nadwozia dla miejskiego auta jest na tyle zaskakująco pojemny ,że spakowanie wszelkich codziennych sprawunków nie jest problemem jak i pakunków na weekendowy wyjazd za miasto nie sprawi Ci żadnego kłopotu! Reasumując przedstawiam Ci do kupna prawie nowe autko na długie lata bezpiecznej jazdy ,z minimalnym przebiegiem - 100% i gwarantowanym wpisem na fakturze nabycia jako wóz jakiego szukasz w rozsądnej cenie ,który ma pierwszy lakier na całym nadwoziu i który nie przechodził żadnych napraw blacharskich ,będący na gwarancji producenta - tak więc czego więcej chcieć w takiej wersji na tak rozsądne pieniądze... <br /> Na wyposażeniu znajdą Państwo między innymi: KLIMATYZACJA Z AUTO-ECO+6xAIR-BAG/KURTYNY+SRS+SRP+ABS+ESP+TPMS+EPS+EPC<br /> +EBD+TEMPOMAT+REGUL.OGRANICZNIK PRĘDKOŚCI+KOMPUTER POKŁADOWY+POLSKIE MENU+ASYSTENCI WSPOMAGANIA RUSZANIA ,JAZDY ,PROWADZENIA I HAMOWANIA+ELEKTRYCZNIE OTWIERANE SZYBY+IMOBILIZER W KLUCZYKU+CENTRALNY ZAMEK+ELEKTR.GRZANE I REGULOWANE LUSTRA ZEWN.+TRWALE OCYNKOWANE NADWOZIE+ZEWN.TEMOMETR Z OSTRZEGANIEM O GOŁOLEDZI+OBROTOMIERZ+ZEGAR+DATA+START/STOP-ROZŁĄCZANY Z ECO+SKRZYNIA MANULANA 5 STOPNIOWA+PODŁOKIETNIK+BDB WYPOROFILOOWANE FOTELE - WYGODNE Z PEŁNYM ISOFIX Z PELNYMI REGULACJAMI POŁOŻEŃ+SZYBY ATERMICZNE Z FILTREM UV - BARWIONE+DZIELONE I ROZKŁADANE TYLNE FOTELE+4 ZAGŁOWKI+DODOTKOWE PASY-KID+BLOKADA ZAMKÓW ELEKTR.I DRZWI TYLNYCH MANULANA DLA DZIECI+KAMERA FRONT DLA KONTROLI NAGŁEGO HAMOWANIA I PILNOWANIA TORU JAZDY W PASIE+DZIENNE ŚWIATŁA DRL-LED+ŚWIATŁA Z AUTO+LED PODŚWIETLENIE WNĘTRZA+SYSTEM POWIADAMIANIA I AUTO-LOKALIZACJI POJAZDU PO WYPADKU (SOS) I WYSYŁANIA SŁUŻB RATUNKOWYCH+PEŁNE AUDIO Z DUZYM TABLETEM DOTYKOWYM COLOR-LED Z TUNER/RDS/AUX/USB/BLUETOOTH MUSIC-GSM/ZESTAW GŁOŚNOMÓWIĄCY TEL.KOM/STEROWANIE AUDIO W KIEROWNICY/ANDROID GSM Z APPLE CAR GSM/INTERNET/SYSTEM NAWIGACJI Z TELEFONU NA TABLET+BDB PEŁNE NAGŁOŚNIENIE WNĘTRZA+SKÓRZANA WIELOFUNKCYJNA KIEROWNICA+ACTIV WSPOMAGANIE KIEROWNICY+REGUL.WYSKOŚCI ŚWIATEŁ ,PASÓW ,FOTELA KIEROWCY I KIEROWNICY + EURO 6 ORAZ INNE EXTRA CUDEŃKA DEDYKOWANE DLA TEGO MODELU HYUNDAIA i10...<br /> <br /> KILKA ZDJĘĆ NA KOŃCU TO ZDJĘCIA Z OFERTY ZAGRANICZNEJ Z KTÓREJ KUPIONO AUTO POZOSTAWIONE JAKO UŻYWANE W SALONIE SPRZEDAZY.<br /> <br /> UMOŻLIWIAM PRZED ZAKUPEM NA KOSZT NABYWCY WERYFIKACJE STANU AUTA PRZEZ ZAMÓWIONEGO KU TEMU RZECZOZNAWCE...<br /> <br /> GORĄCO POLECAM I ZAPRASZAM DO OBEJRZENIA AUTA ,NA PRZEJAŻDŻKĘ I DO ZAKUPU!!! JAKI PRZEBIEG - TAKI STAN!!!<br /> STAN AUTA WZOROWY!!! KTO KUPI BĘDZIE ZADOWOLONY!!!<br /> <br /> MOŻLIWA ZAMIANA NA INNY POJAZD!!!<br /> <br /> KUPUJĄCY JEST ZWOLNIONY Z OPŁATY SKARBOWEJ PO KUPNIE W U.S.<br /> <br /> TEL.KONT.  lub  DZWOŃ!!! ZAPRASZAM!!!",
        "price": 54000,
        "milage": 10900,
        "model": "i10",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 898705883,
        "title": "Hyundai Kona AUTOMAT HYUNDAI KONA 1.6 hybrid 141 koni pełne wyposażenie VAT 23%.",
        "description": "Sprzedam bardzo ładnego Hyundai Kona 1600 benzyna plus hybryda łącznie silniki mają 141 koni skrzynia automatyczna rok 2022 Kwiecień.<br /> <br /> SPALANIE  MIASTO OK 5 LITRÓW.<br /> <br /> WYSTAWIAM FAK VAT 23%.<br /> <br /> JEST TO NASZ PRYWATNY SAMOCHÓD STAN IDEALNY NIE WYMAGA NAKŁADÓW.<br /> <br /> OSTATNI SERWIS OLEJOWY W ASO PRZY 8 TYS KM.<br /> <br /> SAMOCHÓD SPRZEDAWANY Z POWODU KUPNA NOWEGO.<br /> <br /> TEN EGZEMPLARZ NA PEWNO NOWEMU NABYWCY DŁUGO POSŁUŻY CENA ADEKWATNA DO STANU.<br /> <br /> GWARANCJA  KILOMETRÓW WPISUJĘ W UMOWĘ.<br /> <br /> WIZUALNIE I TECHNICZNIE PERFEKCYJNY.<br /> <br />  WNĘTRZE JEST JAK NOWE.<br /> <br /> LAKIER IDEALNY NA CAŁYM SAMOCHODZIE.<br /> <br /> FOTKI Z ZAKUPU DO WGLĄDU MALOWANA MASKA PRAWY PRZEDNI BŁOTNIK.<br /> <br /> OKAZJA NAPRAWDĘ WARTO PIĘKNIE UTRZYMANY TECHNICZNIE I WIZUALNE.<br /> <br /> UWAGA zgadzam się na sprawdzenie auta w Serwisie lub wybranym warsztacie.<br /> <br /> Silnik oraz skrzynia działają wyśmienicie.<br /> <br /> W aucie wszystko sprawne i działające,stan techniczny i wizualny idealny<br /> <br /> AUTO WYPOSAŻONE JEST W DOKŁADNE PROSZĘ SPRAWDZIĆ PO NUMERZE NADWOZIA.<br /> <br /> -Skrzynia automatyczna.<br /> -Kamery<br /> -System nawigacji.<br /> -Czujniki parkowani.<br /> -Centralny zamek.<br /> -Wspomaganie kierownicy.<br /> -Abs.<br /> -Esp<br /> -Airbag<br /> -Klimatyzacja.<br /> -Immobiliser.<br /> -Tempomat.<br /> -Klucze szt 2.<br /> -Radio<br /> -Elektryczne szyby.<br /> -Elektryczne i podgrzewane lusterka.<br /> -Alu felgi.<br /> -Ustawianie kierownicy w dwóch płaszczyznach.<br /> -Komputer pokładowy.<br /> <br /> Do obejrzenia Pierściec ul Jaśminowa 3 woj Śląskie tel",
        "price": 104550,
        "milage": 8898,
        "model": "Kona",
        "condition": "Nieuszkodzony",
        "country_origin": "Czechy",
    },
    {
        "clasfieds_id": 900037928,
        "title": "Hyundai i30 N Performance Auto na Gwarancji Serwisowane",
        "description": "Hyundai w wersji performance - 280KM, szpera, większe hamulce, 19 calowe felgi oraz piękny kolor Performance blue.<br /> Auto po 2 przeglądzie z wymianą oleju i filtrów  27.06.2023 przy przebiegu 19800km, auto jest na 5 letniej gwarancji Hyundai Polska która obejmuje silnik oraz karoserię.   <br /> <br /> Hyundai jest wyposażony w manualną skrzynie biegów co w połączeniu z mocą 280 km oraz precyzyjnym układem kierowniczym, aktywnym zawieszeniem, szperą daje super radość z jazdy, a w dodatku aktywny układ wydechowy daję piękny rasowy dźwięk.<br /> <br /> Szczegółowe informacje przekażę w rozmowie telefonicznej(nie odpowiadam na SMS i komunikatory)",
        "price": 139000,
        "milage": 24500,
        "model": "Pozostałe Hyundai",
        "condition": "Nieuszkodzony",
        "country_origin": "Niemcy",
    },
    {
        "clasfieds_id": 862851749,
        "title": "Kia Optima Nowoczesny, dynamiczny komfortowy, ekonomiczny (Kia Optima Plug- in)",
        "description": "Witam,<br /> Piękna Kia Optima XL plug in -Aurora Black perłowy . Stan bardzo dobry.<br /> Samochód cechuje się niezwykłą przestronnością wewnątrz i komfortem jazdy przy bardzo niskim spalaniu pomimo 205 koni mechanicznych. Średnio przy spokojnej jeździe tylko w trybie hybrydowym  spalanie ok 5 litrów/100km. Dojazdy do ok 62 km pokonuje tylko przy pomocy silnika  elektrycznego i to do prędkości 120 km/h. Ja osobiście całymi miesiącami jeździłem nim praktycznie jako samochodem elektrycznym i z ulgą w portfelu :-)  !!! Bardzo dynamiczny. <br /> Nie posiada uszkodzeń mechanicznych.  Wszelkie przeglądy wykonywane były na bieżąco w tym niezbędna wymiana płynów i filtrów itp.  (ostatnia w  końcu lipca 2023)  (do wglądu rachunek). <br /> Samochód sprowadzono dla mnie na użytek własny z Danii. Niewybity na  naszych drogach :-) . Zawieszenie bardzo dobre bez jakichkolwiek śladów zużycia. Nowe drogie i super dobre opony wielosezonowe Michelin Cross Climate. Posiada udokumentowany przebieg 60 780 km. Samochód posiada bardzo bogate wyposażenie, między innymi takie jak:<br /> - elektryczny fotel kierowcy z funkcją pamięci i super bocznym trzymaniem,  <br /> - grzane fotele przednie, ogrzewana kierownica skórzana. <br /> - asystent utrzymywania pasa ruchu,<br /> - funkcja stop and go, tempomat adaptacyjny, działający idealnie sam utrzymuje się na pasie ruchu i kieruje pojazdem przyspieszając i zwalniając na podstawie odczytu super działającego radaru !<br /> - kamera cofania, czujniki cofania,<br /> - oświetlenie matrycowe LED (widoczność jak w dzień :-))<br /> - ładowarka indukcyjna do telefonu<br /> Na wyposażeniu oczywiście ładowarka typ 2.  <br /> Dodatkowo dokupiłem zdejmowany hak holowniczy za 2200 zł. Nie został niestety użyty bo miał służyć do przewozu rowerów ale nie było czasu. Wejścia na hak normalnie w ogóle nie widać bo jest montowane od spodu.  <br /> Samochód naprawdę zadbany, bardzo dobrze się prezentuje. Nie wymaga żadnego wkładu finansowego. Samochód nie będzie już eksploatowany i będzie czekał na nowego właściciela w garażu. Do tej pory też był garażowany. Nikt w nim nie palił papierosów! <br /> W cenie wysokiej klasy kamera 70 Mai zamontowana profesjonalnie za lusterkiem wstecznym. <br /> Cena do małej negocjacji.<br /> Wyrażam zgodę na dokonanie przeglądu na dowolnej stacji diagnostycznej, a także u autoryzowanego dealera KIA. <br /> Sprzedaję z uwagi na zakup w ostatnim czasie służbowego samochodu elektrycznego, który wykorzystuję też prywatnie .",
        "price": 91000,
        "milage": 60780,
        "model": "Optima",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 897742680,
        "title": "Kia Ceed Automat, Kamera, PDC ASO KIA serwis, bardzo ładne i zadbane auto",
        "description": "ładne ,Zadbane auto  faktura vat -marża<br /> servis ASO <br /> -auto zarejestrowane w Polsce<br /> - KAMERA<br /> -Czujniki parkowania tył<br /> -Automatyczne wycieraczki<br /> -regulowane tryby jazdy<br /> - dwa kompletu kluczyków<br /> • Reflektory automatyczne xenon<br /> • Skórzana kierownica<br /> • Start/Stop system<br /> • Zamek centralny - FB<br /> - Doświetlanie zakrętów<br /> - Fotele – podgrzewany fotel kierowcy i pasażera<br /> - Line Assist<br /> - Side Assist<br /> - samochód nie wymaga wkładu finansowego<br /> tel",
        "price": 67500,
        "milage": 122000,
        "model": "Cee'd",
        "condition": "Nieuszkodzony",
        "country_origin": "Niemcy",
    },
    {
        "clasfieds_id": 889901163,
        "title": "Mercedes-Benz Klasa S",
        "description": "Sprzedam Mercedes-Bezn S Coupe S63 AMG Wersja po Liftingu<br /> Pojemnos: 4.0 Benzyna Moc: 612KM Oryginalny, udokumentowany przebieg: 50800km<br /> Bardzo bogata wersja wyposazenie min:<br /> -AMG PAKIET CARBON wewnatrzny i zewnatrzny<br /> -Climatronic<br /> -Podgrzewane, wentylowane, el. regulowane z pamiecia fotele<br /> -Head-up<br /> -Pakiet KEYLESS-GO<br /> -Pakiet komfort cieplny z podgrzewaną kierownicą<br /> -Czarna podsufitka obszyta alcantara<br /> -Pakiet parkowania z kamerą 360°,<br /> -Distronic<br /> -Kierownica AMG Performance pokryta skora+mikrofibra<br /> -Oswietlenie Ambiente<br /> -Naglosnienie Burmester<br /> -Pakiet antykradzieżowy z przygotowaniem do zgłoszenia szkody na<br /> parkingu<br /> -Podwójny uchwyt na kubki z przodu<br /> -Tuner TV<br /> -Lusterka fotochrom<br /> -Webasto sterowane z pilota<br /> -System otwierania drzwi garazowych<br /> -El. szyby<br /> -El. regulowane i skladane lusterka<br /> -El. tylna roleta<br /> -Panoramiczny dach<br /> -Wysokowydajny kompozytowy układ hamulcowy AMG CERAMIC<br /> -10-ramienne kute obręcze kół AMG o średnicy 20 cali w kolorze<br /> tytanowej szarości i polerowane<br /> I wiele,wiele innych. Dla zaineteresowanych udostepnie nr VIN .<br /> Auto sprowadzone z niemiec od pierwszego wlasciciela. Przebieg udokumentowany+ komplet oryginalnych kluczykow wraz z pilotem od Webasto. Stan auta uwazam za IDEALNY, nie wymaga zadnego wkladu finansowego. Polecam bo naprawde warto!!!<br /> Zapraszam na ogledziny i jazde probna.<br /> Więcej info pod numerem",
        "price": 577777,
        "milage": 51500,
        "model": "S Klasa",
        "condition": "Nieuszkodzony",
        "country_origin": "Niemcy",
    },
    {
        "clasfieds_id": 826513938,
        "title": "Mitsubishi Colt 1,3 Pb + Lpg ekonomiczny spalanie od 5 l / 100 km klima elektryka",
        "description": "1,3 Pb   + instalacja Gazowa<br /> <br /> atest  LPG   - do 2030<br /> <br /> moc silnika 95 KM<br /> <br /> małe spalanie od 5 l  gazu   / 100 km przy ekonomicznej jeżdzie<br /> <br /> instalacja sekwencyjna LPG  <br /> <br /> nadwozie w ładnym stanie<br /> <br /> środek ładny<br /> <br /> kolor szary metalik <br /> <br /> klimatyzacja<br /> <br /> alufelgi<br /> <br /> elektryka<br /> <br /> lokalizacja : Kraków  Nowa Huta<br /> <br />  proszę dzwonić lub pisać sms    z braku czasu nie pilnuję zbytnio maili - zainteresowany - proszę dzwonić lub pisać sms",
        "price": 11400,
        "milage": 230000,
        "model": "Colt",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 904730346,
        "title": "Nissan X-Trail Kamera 360, asysten pasa ruchu, szklany dach, Stan jak nowy. Zapraszam",
        "description": "Auto bardzo dobrym stanie techniczym i wizualnym. Piersza rejestracja 24,02,2022r. <br /> Do auta jest drugi komplet kol zimowych. 2x kluczyki ksiazki serwisowe. Obecnie po wymianie oleju i filtrow. <br /> obecnie w trakcie rejstrownia w Polsce. Zapraszam do obejrzenia w Markach kolo Warszawy.  tel.",
        "price": 109900,
        "milage": 34950,
        "model": "X-Trail",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 899624023,
        "title": "Nissan Qashqai Bogate wyposażenie",
        "description": "Pojazd w bardzo dobrym stanie, zadbany.<br /> Sprowadzony z Hiszpani ,zarejestrowany w kraju.<br /> Oc ,przegląd aktualne.<br /> Dwa klucze ,komplet dokumentów.<br /> Lakier cały w oryginale.<br /> Przebieg dopisze na fakturze.<br /> Auto w 100% sprawne nie wymaga nakładów finansowych.<br /> Wymienione filtry ,oleje oraz zrobiony serwis klimatyzacji.<br /> <br /> Na wyposażeniu:<br /> <br /> -Ledy<br /> -Isofix<br /> -Keyless<br /> -Nawigacja<br /> -Halogeny<br /> -Alufelgi 18&amp;#039;&amp;#039;<br /> -Kamery 360<br /> -Tempomat<br /> -Bluetooth<br /> -Start / stop<br /> -Składane lusterka<br /> -Panoramiczny dach<br /> -Asystent pasa ruchu<br /> -Sześć poduszek powietrznych<br /> -Czujnik deszczu / zmierzchu<br /> -Klimatyzacja dwustrefowa<br /> -Czujniki parkowania przód / tył<br /> -Skórzana kierownica wielofunkcyjna<br /> itd...<br /> <br /> Na pytania odpowiem telefonicznie.<br /> <br /> Samochód po wszystkich opłatach.<br /> Koszt rejestracji 160zł.<br /> Możliwość sprawdzenia samochodu na stacji diagnostycznej lub po wcześniejszym umówieniu się w autoryzowanym serwisie.<br /> Kupujący zwolniony z opłaty skarbowej.",
        "price": 79900,
        "milage": 91000,
        "model": "Qashqai",
        "condition": "Nieuszkodzony",
        "country_origin": "Hiszpania",
    },
    {
        "clasfieds_id": 874483437,
        "title": "Suzuki Ignis (Nr. 140) 1.2 Hybrid Kamera Klimatyzacja Tempomat Gwarancja!!!",
        "description": "Auto Komis E8   ul. Sienkiewicza 31, 62-400 Słupca<br /> Jeden z największych sprzedawców samochodów używanych w Wielkopolsce.<br /> W ciągłej sprzedaży około 200 aut. Działamy w branży motoryzacyjnej od 20 lat.<br /> Wypracowane przez nas doświadczenie sprawia , że możemy dokładnie sprawdzić auto przed sprzedażą<br /> i udzielić na nie 12 miesięcznej gwarancji z możliwością rozszerzenia do 2 lat.<br /> <br /> - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - <br /> <br /> WYPOSAŻENIE AUTA<br /> <br /> - 6 x Airbag<br /> - Elektryczne szyby<br /> - Elektrycznie regulowane lusterka<br /> - Klimatyzacja manualna<br /> - Centralny zamek z pilotem<br /> - Radio CD<br /> - Sterowanie radia w kierownicy<br /> - Komputer pokładowy<br /> - Tempomat<br /> - Wspomaganie kierownicy<br /> - ABS <br /> - Immobilizer<br /> - Relingi dachowe<br /> - Aluminiowe felgi<br /> - Podgrzewane fotele<br /> - Materiałowa tapicerka<br /> - Kamera parkowania<br /> - Skórzana tapicerka<br /> - Światła do jazdy dziennej w technologi Led<br /> - ESP<br /> <br /> Udokumentowany Przebieg !!!<br /> <br /> Auto przygotowane do rejestracji !!!<br /> <br /> - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -<br /> <br /> Możliwość pozostawienia swojego auta w rozliczeniu<br /> <br /> - - - - -  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -<br /> <br />    Możliwość zakupu na raty  <br />    Uproszczone procedury kredytowe<br /> <br /> informacje kredytowe <br /> <br /> - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -<br /> <br /> Pojazd z GWARANCJĄ VIP Gwarant, zapewni Państwu ochronę <br /> przed nieprzewidzianymi wydatkami związanymi <br /> z usuwaniem awarii w okresie 12 miesięcy.<br /> <br /> Bezgotówkowy system napraw, auta zastępcze dla Klientów oraz całodobowa Pomoc Drogowa<br /> w Programie VIP Assistance zapewnią Państwu spokój <br /> i bezpieczeństwo w trakcie użytkowania pojazdu.<br /> <br /> Podzespoły objęte Gwarancją VIP Gwarant:<br /> <br />  + silnik <br />  + silnik hybrydowy<br />  + skrzynia biegów manualna <br />  + skrzynia biegów automatyczna <br />  + bezstopniowa skrzynia biegów <br />  + koło zamachowe dwumasowe <br />  + turbina lub turbosprężarka <br />  + rozrusznik <br />  + alternator <br />  + układ hamulcowy <br />  + układ chłodzenia <br />  + komputer główny silnika <br />  + łańcuch rozrządu <br />  + pasek rozrządu (uszkodzenie silnika w przypadku pęknięcia, zerwania lub zsunięcia paska) <br />  + zawieszenie pneumatyczne <br />  + zawieszenie mechaniczne <br />  + zawieszenie komfortowe <br />  + przekładnia hydrokinetyczna <br />  + mechanizmy różnicowe <br />  + wał pędny <br />  + filtr cząstek stałych DPF <br />  + obudowy podzespołów - skrzyni biegów, silnika, miski olejowej itp. <br />  + materiały eksploatacyjne <br />  + pakiet części <br />  + pojazd zastępczy na czas naprawy <br />  + VIP ACOC - bezgotówkowa pomoc przy likwidacji szkód komunikacyjnych <br />  + naprawy warsztatowe <br />  + diagnoza i weryfikacja <br />  + naprawy na drodze <br />  + pomoc ASSISTANCE: <br />    w przy przebiciu ogumienia, <br />    rozładowaniu akumulatora, <br />    zatrzaśnięciu auta, <br />    awarii alarmu lub immobilisera, <br />    a nawet jak zabraknie Państwu paliwa na drodze <br />  <br />  ++ Brak limitów ilości napraw w czasie trwania Gwarancji VIP <br />  ++ Bezpłatna konsultacja ze specjalistami technicznymi w razie wystąpienia awarii <br />  ++ Naprawy w autoryzowanych serwisach na terenie Polski <br />  ++ Najkrótszy czas rozpatrzenia awarii i zatwierdzenia naprawy - do 24 h <br />  ++ Już ponad 40 000 zadowolonych Klientów <br />  ++ Przejrzysty Certyfikat/Karta Gwarancyjna obrazująca podzespoły objęte Gwarancją <br />     w wybranym przez Klienta Pakiecie Usług <br />  ++ Bezpieczeństwo i komfort w podróżach  <br /> <br /> Zadzwoń i spytaj o szczegóły !<br /> <br /> Możliwość sprawdzenia auta na stacji diagnostycznej lub w autoryzowanym serwisie !!!<br /> <br /> - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - <br /> <br /> . TEL. KONTAKTOWE <br />      <br /> . <br /> <br /> . <br /> <br /> - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - <br /> <br /> AUTO KOMIS E8 ZNAJDUJE SIĘ:<br /> <br /> -  70 km od Poznania<br /> - 230 km od Warszawy<br /> - 120 km od Torunia<br /> - 130 km od Łodzi<br /> - 180 km od Wrocławia<br /> <br /> Wszelkie informacje zawarte na niniejszej stronie internetowej nie stanowią oferty w rozumieniu Kodeksu Cywilnego. <br /> W wypadku sprzedaży konsumenckiej w rozumieniu ustawy z dnia 27 lipca 2002 r. o szczególnych warunkach sprzedaży konsumenckiej <br /> oraz o zmianie Kodeksu cywilnego (dalej: Ustawa), zawarte na niniejszej stronie internetowej informacje nie stanowią zapewnienia <br /> w rozumieniu art. 4 ust. 3 Ustawy, jak również nie stanowią opisu towaru w rozumieniu art. 4 ust. 2 Ustawy. <br /> Indywidualne uzgodnienie ceny i wyposażenia pojazdu następuje w umowie jego sprzedaż.<br /> <br /> 44FOX-ID: 859",
        "price": 59900,
        "milage": 19000,
        "model": "Ignis",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 889127564,
        "title": "Volvo S80 Volvo S80. Bogata wersja, zadbany, oryginalny przebieg",
        "description": "Witam. Mam do sprzedania Volvo S80 z 2011 roku. Mechanicznie i elektrycznie samochód jest w 100% sprawny. Fantastyczny silnik R6 3.2 pracuje idealnie i zapewnia niesamowita wrażenia z jazdy. Skrzynia pracuje bardzo dobrze. Samochód nie ma żadnych wycieków. Przebieg jest w milach.<br /> Kolor samochodu z pozoru to czarny, jednak odpowiednie światło uwydatnia perłowy lakier, który wchodzi w kolor brązowy. Wnętrze jest bardzo zadbane, a skórzana tapicerka jest niemal w idealnym stanie. Lakier na masce i przednim zderzaku nieco ucierpiał (są to zwykłe odpryski lakieru powstałe w czasie eksploatacji pojazdu. Maska jednym miejscu jest delikatnie zagięta, co widać na zdjęciu. Wszystkie szyby (za wyjątkiem czołowej) są oryginalne. Na wyposażeniu znajdują się oryginalne materiałowe dywaniki, a na nich położone są gumowe ze względu na praktyczność w zimę.<br /> Auto było regularnie serwisowane. Ostatnio wymieniony olej silnikowy i wszystkie filtry, a także olej w skrzyni biegów. Olej silnikowy to Valovline 5W30 dedykowany do tego samochodu. Przyszłego właściciela czeka wymiana tarcz i klocków hamulcowych, ponieważ na tych zaczął już robić się rant, dlatego cena jest odpowiednio niższa ;) Samochód użytkował mój tata, a sprzedaje ponieważ kupił sobie młodsze Volvo. W razie pytań proszę dzwonić.",
        "price": 34200,
        "milage": 195000,
        "model": "S80",
        "condition": "Nieuszkodzony",
        "country_origin": "Stany Zjednoczone",
    },
    {
        "clasfieds_id": 900042182,
        "title": "lexus nx 300h  4x4 executive line",
        "description": "Witam sprzedam LEXUSA NX 300h z silnikiem 2,5 benzyna hybryda auto sprowadzone z Hiszpani 16.05.2023r. Jestem pierwszym właścicielem w Polsce Lexus sprawuję się bardzo fajnie jest dobrze wyposażony ma skórzaną tapicerkie ,nawigacje ,tępomat aktywny z radarem ,klimatyzację i wiele innych bajerów zainteresowanych proszę o kontakt tel.6******07 pozdrawiam Andrzej",
        "price": 114000,
        "milage": 81000,
        "model": "Pozostałe Lexus",
        "condition": "Nieuszkodzony",
        "country_origin": "Hiszpania",
    },
    {
        "clasfieds_id": 823023618,
        "title": "Jeep Grand Cherokee Jeep Grand Cherokee Gr 3.6 V6 Overland",
        "description": "Witam, mam do sprzedania samochód marki Jeep Grand Cherokee:<br /> <br /> - Bardzo niski przebieg 39k <br /> - rok produkcji: 2018<br /> - nowa instalacja LPG<br /> - silnik: 3.6 VVT <br /> - skrzynia biegów: automatyczna , 8-śmio biegowa,<br /> - Opłacony<br /> - zarejestrowany<br /> nr vin: 1C4RJFBG2JC322432<br /> <br /> Więcej informacji pod numerem:<br /> - <br /> <br /> Możliwy transport !!!<br /> <br /> Godziny otwarcia:<br /> pn. - pt. 8-16,<br /> sob. możliwa po wcześniejszym kontakcie telefonicznym<br /> <br /> email. przyczepy25wp.pl",
        "price": 123000,
        "milage": 39198,
        "model": "Grand Cherokee",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 898016300,
        "title": "Seat Ateca 1.5 TSI Style Faktura Vat23",
        "description": "Sprzedam Seata Ateca z silnikiem benzynowym 1.5 TSI o mocy 150 koni i manualną 6 biegową skrzynią biegów w wersji wyposażenia style. Konfiguracja za 141 543 zł.<br /> Samochód w idealnym stanie, tylko 4800 km przebiegu.<br /> Bezwypadkowy.<br /> 5 lat gwarancji lub do przebiegu 100tys. km (pierwsze 2 lata bez limitu), początek gwarancji 21.02.2023<br /> Przy przebiegu 3560 km silnik został wymieniony na nowy na podstawie gwarancji w ASO.<br /> Wystawiam fakturę Vat 23% - 87 724 zł netto.<br /> Kupujący zwolniony z podatku PCC 2%.<br /> Możliwy leasing lub kredyt.<br /> Wyposażenie:<br /> Koła<br /> 17-calowe felgi aluminiowe DYNAMIC 36/1 215/55 R17 94V z oponami zimowymi.<br /> Dodatkowo komplet opon letnich.<br /> Systemy wspomagające kierowcę<br /> System kontroli odstępu Front Assist z funkcją awaryjnego hamowania i funkcją ochrony pieszych<br /> System rozpoznawania zmęczenia<br /> Ogranicznik prędkości i tempomat<br /> System kontroli ciśnienia powietrza w oponach<br /> Asystent podjazdu (Hill Hold Control); Funkcja rekomendacji zmiany biegów<br /> Czujniki parkowania z tyłu z optycznym systemem parkowania<br /> System powiadamiania ratunkowego eCall<br /> Bezpieczeństwo<br /> ABS, ESC, ASR, EDL, BAS, HBA<br /> XDS-Elektroniczn blokada mechanizmu róznicowego<br /> 7 poduszek powietrznych (2 przednie, 2 boczne, 2 kurtyny powietrzne, poduszka kolanowa kierowcy) z dezaktywacją poduszki powietrznej pasażera<br /> Zagłówek fotela kierowcy i pasażera z systemem WOKS<br /> System przypominający o konieczności zapinania pasów przy przednich i tylnych fotelach<br /> Zaczepy ISOFIX i Top Tether przy siedzeniach tylnej kanapy (dla 2 fotelików dziecięcych)<br /> Komfort<br /> Automatyczna klimatyzacja dwustrefowa Climatronic<br /> Elektromechaniczny hamulec postojowy<br /> Pakiet praktyczny: Czujnik deszczu; Czujnik zmierzchu (automatyczne światła); Automatyczna funkcja opóźnionego wyłączania świateł „Coming and Leaving Home”; Automatycznie ściemniające się lusterko wsteczne; Automatycznie obniżające się lusterko pasażera podczas cofania<br /> Elektrycznie sterowane szyby boczne z przodu i z tyłu<br /> Elektrycznie regulowane, podgrzewane i składane lusterka boczne<br /> Centralny zamek ze zdalnym sterowaniem, dwa składane kluczyki, otwieranie klapy bagażnika z pilota (3 przyciski) oraz system bezkluczykowego uruchamiania samochodu KESSY GO<br /> Multimedia<br /> DAB (Digital Audio Broadcasting - funkcja odbioru programów radiowych w formie cyfrowej<br /> Oświetlenie<br /> Pełne przednie światła LED<br /> Światła do jazdy dziennej LED oraz tylne światła LED<br /> Przednie światła przeciwmgielne LED z funkcją doświetlania zakrętów<br /> Nadwozie<br /> Zewnętrzny pakiet BLACK: Czarne relingi dachowe; Czarne elementy ochronne nadkoli<br /> Lusterka boczne i klamki w kolorze nadwozia; Obramowanie osłony chłodnicy w kolorze chromu; Antena dachowa w kształcie płetwy rekina<br /> Czarne relingi dachowe<br /> Wnętrze - fotele i elementy ozdobne<br /> Przednie fotele typu Comfort<br /> Fotel kierowcy i pasażera z regulacją wysokości<br /> Fotel kierowcy i pasażera z regulacją wysokości i podparcia odcinka lędźwiowego<br /> Elementy dekoracyjne deski rozdzielczej w kolorze chromu; Wnętrze Style z szarymi elementami dekoracyjnymi konsoli środkowej; Dywaniki welurowe z przodu i z tyłu<br /> Wnętrze - kierownice<br /> Sportowa kierownica wielofunkcyjna obszyta skórą<br /> Wyposażenie dodatkowe:<br /> Pakiet wspomagania jazdy M dla samochodów z Navi System+<br /> / Asystent pasa ruchu Lane Assist / Asystent świateł drogowych High Beam Assist / Predykcyjny tempomat (ACC): dostosowanie prędkości jazdy do znaków drogowych i danych nawigacji / System rozpoznawania znaków drogowych<br /> Asystent parkowania z czujnikami parkowania z przodu i z tyłu<br /> Czujniki parkowania z tyłu i przodu, asystent parkowania<br /> Wirtualny kokpit: cyfrowa tablica przyrządów z kolorowym ekranem TFT 10,25”<br /> Navi System+<br /> Nawigacja satelitarna z mapami Europy; 9,2-calowy kolorowy ekran dotykowy z czujnikiem zbliżeniowym; 2 podświetlane gniazda USB typu C z przodu i 2 x USB z tyłu do ładowania urządzeń; 8 głośników; Rozbudowana funkcja rozpoznawania mowy i sterowania głosem; WLAN<br /> Schowek z funkcją bezprzewodowego ładowania telefonu i wzmacniaczem sygnału<br /> Przyciemniane szyby<br /> Funkcja łatwego składania tylnych siedzeń<br /> Pakiet schowków<br /> Schowki pod przednimi fotelami",
        "price": 107900,
        "milage": 4800,
        "model": "Pozostałe Seat",
        "condition": "Nieuszkodzony",
        "country_origin": "Hiszpania",
    },
    {
        "clasfieds_id": 828979997,
        "title": "Mazda 6 Mazda 6 gj 2016r polift.Tylko 63 tys km.max opcja.",
        "description": "Witam serdecznie. Sprzedam Mazde 6 GJ z 2016 roku polift. Max wyposażone head up display, radar,skora aktywny tempomat system naglosnienia bose i wiele innyych. Auto przyprowadzone ze Stanow Zjednoczonych jestem pierwszym właścicielem w kraju. Auto z bardzo malym przebiegiem 63800 km bardzo dobrze wyposażone, nie wymaga zadnego wkladu finansowego. Świeżo po serwisie filtrowo olejowym, OC jak i PT oplacone na rok.Prosze tylko konkretnie zainteresowane osoby szanuje swoj i Państwa czas. Cena do negocjacji po obejrzeniu auta i jezdzie probnej.Wiecej informacji na temat auta udziele telefonicznie. Pozdrawiam.",
        "price": 72900,
        "milage": 63700,
        "model": "6",
        "condition": "Nieuszkodzony",
        "country_origin": "Stany Zjednoczone",
    },
    {
        "clasfieds_id": 889372579,
        "title": "Chrysler Pacifica Chrysler Pacyfica 2022",
        "description": "https://francuskie.pl/chrysler-pacifica-z-wysoka-nota-w-testach-iihs-2023/<br /> <br /> Auto sprowadzone ze Stanów<br /> -Napęd na 4 koła<br /> -Opony 20'<br /> -Odkurzacz,<br /> -Full opcja,<br /> -Szyberdach<br /> PEŁNA FAKTURA VAT-23%,mozliwosc rozliczenia 100% Vat<br /> auto zarejestrowane w Polsce,<br /> dostosowane do wszystkich wymogów europejskich (łącznie z nawigacją)",
        "price": 244900,
        "milage": 16000,
        "model": "Pacifica",
        "condition": "Nieuszkodzony",
        "country_origin": "Stany Zjednoczone",
    },
    {
        "clasfieds_id": 876402773,
        "title": "Mercedes-Benz CLA Ogłoszenie prywante, Przebieg 125000km, FULL LED, PEŁNY SERWIS ASO",
        "description": "MERCEDES BENZ CLA<br /> Rok produkcji: 2017<br /> II WŁAŚCICIEL<br /> Zakup oraz pierwsza rejestracja w czerwcu 2017 roku.<br /> Silnik: 1.6 benzyna 122KM<br /> Przebieg: 125000km<br /> 100% SERWISOWANY w ASO MERCEDES<br /> Witam serdecznie.<br /> Przedmiotem sprzedaży jest moje prywatne auto.<br /> Samochód jest moją własnością, jest zarejestrowany na mnie- nie handluje samochodami.<br /> Samochód o znikomym przebiegu 125000km w pełni udokumentowanym, od początku do końca serwisowany (WYDRUKI Z SERWISÓW ASO), wszystko naprawiane i wymieniane na oryginalnych częściach MERCEDES (posiadam wydruki z ASO). Ostatni serwis wykonany w ASO MERCEDESA w czerwcu 2022 roju przy przebiegu 114487km. <br /> Niedowiarkom udostępnię nr VIN, zachęcam do zweryfikowania wyżej przedstawionej historii w każdym salonie Mercedes w Polsce.<br /> Merceses świeżo po serwisie olejowo filtrowym oraz serwisie układu klimatyzacji (wykonanym w niezależnej stacji obsługi pojazdów), ponadto zamontowano NOWY KOMPLET OPON.<br /> Silnik samochodu spisuje się wzorowo, cieszy znikomym apetytem na paliwo. Samochód z najlepszą, legendarną, bezawaryjną jednostką doładowaną o mocy 122KM, dobrze przyśpiesza i daje frajdę z jazdy. Auto prowadzi się jak nowe.<br /> Wnętrze pojazdu w bardzo dobrym stanie nie odbiega w żadnym stopniu i od auta nowego, plastiki, kierownica, gałka zmiany biegów, przełączniki bez rys i przetarć , tapicerka czysta bez dziur. <br /> Karoseria pojazdu bez korozji, rys, wgnieceń- lakier pięknie lśni co sprawia że auto wygląda atrakcyjnie i świeżo. Nadwozie w głębokim czarnym kolorze. Samochód budzący zazdrość i podziw innych uczestników ruchu drogowego: zjawiskowe, atrakcyjne, zwracające na siebie uwagę.<br /> Samochód posiada ważny przegląd techniczny oraz ubezpieczenie OC do marca 2024r.<br /> Dla przyszłego nabywcy przekazuje pełną dokumentacje serwisową, instrukcje w języku polskim dwa klucze, karta pojazdu, dowód rejestracyjny, wydruki z przeglądów z ASO Merceses.<br /> Wyrażam zgodę na sprawdzenie pojazdu na dowolnie wybranej stacji diagnostycznej.<br /> Samochód do obejrzenia w Kielcach. Zapraszam do kontaktu. Pokaźna galeria 40-stu zdjęć na portalu otomoto.",
        "price": 83800,
        "milage": 125000,
        "model": "CLA",
        "condition": "Nieuszkodzony",
        "country_origin": "Finlandia",
    },
    {
        "clasfieds_id": 889144800,
        "title": "Kia EV6 Kia EV6 GT",
        "description": "Dzień dobry <br /> <br /> Na sprzedaż Kia EV6. Auto z przebiegu 6600 km  <br /> Wersja GT. 585 koni mechanicznych. Pełne wyposażenie. Napęd 4x4. Zainteresowanych proszę o kontakt telefoniczny, odpowiem na wszelkie pytania",
        "price": 209000,
        "milage": 8700,
        "model": "Pozostałe KIA",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 899631615,
        "title": "Nissan Leaf Najbogatsza Wersja 40kWh Bose Skóra Led Navi Kamera 2 Klucze Polska!",
        "description": "Drodzy Klienci, <br /> <br /> Wychodząc naprzeciw Waszym oczekiwaniom, pragniemy poinformować, iż każde sprzedawane przez naszą firmę auto może być objęte 12 miesięcznym programem gwarancyjnym.<br /> <br /> Oferowane pojazdy posiadają pełną oryginalna historię serwisową co w wiekszości przypadków potwierdzone jest dokumentami lub zapisem cyfrowym przeglądów. <br /> <br /> Każde sprzedawane przez naszą firmę auto jest wyselekcjonowane z pośród wielu. <br /> Ponieważ bardzo cenimy Państwa czas i pieniądze - szczególną wagę przykładamy do stanu technicznego każdego pojazdu.<br /> <br /> O szczegóły zapytaj sprzedawcę.<br /> <br /> NISSAN LEAF 40 kWh 150KM - 2018 ROK!<br /> <br /> ## AUTO OPŁACONE - ZAREJESTROWANE I UBEZPIECZONE W POLSCE  ##<br /> <br /> ## GWARANCJA ORYGINALNEGO PRZEBIEGU - 102.000KM ##<br /> <br /> ## 2 ORYGINALNE KOMPLETY KLUCZY ##<br /> <br /> ## 2 ŁADOWARKI W ZESTAWIE ##<br /> <br /> ### NAJBOGATSZA WERSJA WYPOSAŻENIA ###<br /> <br /> ### NAWIGACJA Z MAPAMI POLSKI # KAMERA 360 # NAGŁOŚNIENIE BOSE # LAMPY LED # CZUJNIKI PARKOWANIA PRZÓD / TYŁ # SKÓRZANA TAPICERKA #  4 X PODGRZEWANE FOTELE # PODGRZEWANA KIEROWNICA # ROZBUDOWANY KOMPUTER POKŁADOWY # DUŻY WYŚWIETLACZ MULTIMEDIALNY #  ZESTAW GŁOŚNOMÓWIĄCY BLUETOOTH # TEMPOMAT # SYSTEM BEZKLUCZYKOWY - KEYLESS GO # ORYGINALNE ALUFELGI 18 # KLIMATRONIC # WIELE INNYCH DODATKÓW ##<br /> <br /> Stan techniczny jak i wizualny bardzo dobry!<br /> Silnik pracuje rowno, zawieszenie bardzo dobrze utrzymane!<br /> Bez zadnego wkladu finansowego!<br /> <br /> Posiada ważne badanie techniczne i ubezpiecznie!<br /> W pełni gotowe do jazdy!<br /> <br /> Mozliwosc rat - procedura uproszczona.<br /> Kupujacy zwolniony z oplaty skarbowej!<br /> <br /> Sprzedaż - zamiana <br /> Przyjmujemy auta w rozliczeniu na dogodnych warunkach!<br /> Formalności kredytowe - leasingowe na miejscu. <br /> Bezpłatna wycena samochodów.<br /> <br /> Niniejsze ogłoszenie jest wyłącznie informacja handlową i nie stanowi oferty w myśl art. 66, paragraf 1. Kodeksu cywilnego.<br /> Sprzedający nie odpowiada za ewentualne błędy zawarte w ogłoszeniu.<br /> <br /> Zapraszamy!<br /> -<br /> - <br /> <br /> Dodatkowe informacje: liczba poduszek powietrznych: 8, liczba miejsc: 5, tapicerka: skora, tapicerka kolor: czarny, kraj pochodzenia: Dania<br /> <br /> Numer oferty: AKL17X8W9",
        "price": 76900,
        "milage": 102304,
        "model": "Pozostałe Nissan",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 899593733,
        "title": "VW UP! Jedyny taki... 1,0 MPI 2015. Nowy rozrząd!!",
        "description": "Volkswagen UP z niezniszczalnym silnikiem MPI który sprawdza się z instalacją gazowa. Pizzerie robią takimmi autami po 400tys bez awarii... <br /> Volkswagen ma świeżo wymieniony kompletny rozrząd. Także teraz tylko robić kilometry ;) stary z bagażniku do wglądu. <br /> Na Upie jest oryginalny lakier.<br /> W aucue zostały przyciemnione szyby i  oklejone w  profesjonalnej firmie czerwonymi elementami według własnego pomysłu także inny taki na drodze się nie pojawi ;)<br /> Upik ma klimatyzację (świeżo po obsłudze przed sezonem letnim), grzane fotele, grzane lusterka, nawigacje, bluetooth, zestaw głośnomówiący, system start/stop, komputer pokładowy i ...co dla mnie jest bardzo ważne...można słuchać muzyki z telefonu bez kabli...I gra całkiem nieźle ;)<br /> Auto idealne do miasta czy na dojazdy do szkoły czy pracy. Jeżdżę min z dziećmi 8 i 9 lat i same bez problemu siadają we fotelikach bez konieczności przesuwania foteli. A mam 186cm wzrostu....<br /> Autko super mi się sprawdza na dojazdy do pracy i odwiezienia przy tym dzieci do szkoły. <br /> I co najważniejsze bardzo mało pali I wbrew pozorom mocy mu nie brakuje.<br /> Polecam<br /> Na wszelkie pytania odpowiem telefonicznie.",
        "price": 24800,
        "milage": 195000,
        "model": "Up!",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 895607558,
        "title": "Peugeot 208 1.2 benz. 75KM Gwarancja Zamiana Zarejestrowany",
        "description": "Peugeot 208<br /> 1.2 benzyna 75KM<br /> Skrzynia biegów manualna <br /> Rok prod. 2020<br /> Przebieg 49 tys. km<br /> <br /> Auto zarejestrowane w Polsce<br /> <br /> WYPOSAŻENIE:<br /> Airbag x6<br /> Wspomaganie kierownicy<br /> Centralny zamek + pilot<br /> El. szyby <br /> El. lusterka <br /> ABS<br /> ESP<br /> Komputer <br /> Tempomat<br /> Ogranicznik <br /> Sensor zmierzchu<br /> Kierownica wielofunkcyjna<br /> Polecenia głosowe<br /> Radio dotykowe MP3 USB + sterowanie w kierownicy<br /> Bluetooth<br /> Nawigacja GPS po podłączeniu z telefonem<br /> Menu w języku polskim<br /> Klimatyzacja<br /> Podgrzewane fotele<br /> Aplikacje internetowe AppleCar AndroidAuto MirrorLink<br /> ISOFIX<br /> START-STOP<br /> Parktronik tył<br /> Światła do jazdy dziennej LED<br /> Oświetlanie drogi do domu<br /> Asystent hamowania<br /> Asystent pasa ruchu<br /> Rozpoznawanie znaków drogowych<br /> Skórzana kierownica<br /> Alarm nieuwagi kierowcy<br /> <br /> Nie odpowiadam na SMS!<br /> Możliwość pozostawienia auta w rozliczeniu!<br /> <br /> Sprawdź naszą pełną ofertę<br /> zadzwoń, chętnie odpowiem na wszystkie pytania!<br /> Atrakcyjne warunki kredytowe!<br /> Kupujący zwolniony z opłaty skarbowej<br /> Zapraszam do oglądania i na jazdę próbną!<br /> <br /> G W A R A N C J A na A U T O - udzielamy 3 miesięcznej gwarancji CAR GWARANT w cenie samochodu.<br /> Gwarancja jest realizowana w sieci serwisowej na terenie całego kraju!<br /> Możliwość przedłużenia gwarancji do 12 miesięcy.<br /> Naprawa i wszystkie części w okresie gwarancji usuwane będą bezpłatnie",
        "price": 49900,
        "milage": 49000,
        "model": "208",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 894465400,
        "title": "Jaguar XE *Suzuki Matsuoka Łódź* Skórzana tapicerka* Kamera* Czujniki* FV23*",
        "description": "Witamy Serdecznie na naszym ogłoszeniu,<br /> <br /> Autoryzowany dealer Suzuki Matsuoka Łódź posiada do zaoferowania samochód Jaguar XE w konfiguracji Pure z silnikiem 2.0 diesel połączonym z napędem 2WD (tył) wraz ze skrzynią manualną 6cio biegową. <br /> <br /> * Nowy rozrząd * <br /> <br /> Autoryzowany Salon i Serwis Suzuki Matsuoka Łódź<br /> 93-408 Łódź ,ul. 3 Maja 1/3<br /> <br /> Kontakt do opiekuna ogłoszenia<br /> <br /> Artur Pokorski <br /> <br /> Wyposażenie min:<br /> - Alufelgi<br /> - Podgrzewane fotele<br /> - Kamera cofania<br /> - Czujniki parkowania<br /> - Elektrycznie ustawiane lusterka<br /> -Elektrycznie regulowane szyby<br /> - Skórzana tapicerka<br /> i wiele innych...<br /> <br /> Autoryzowany Salon i Serwis Suzuki Matsuoka Łódź<br /> 93-408 Łódź ,ul. 3 Maja 1/3<br /> <br /> Kontakt do opiekuna ogłoszenia<br /> <br /> Artur Pokorski <br /> <br /> Niniejsze ogłoszenie jest wyłącznie informacją handlową i nie stanowi oferty w myśl art. 66§1 Kodeksu Cywilnego. Sprzedający nie odpowiada za ewentualne błędy lub nieaktualność ogłoszenia.",
        "price": 49900,
        "milage": 212720,
        "model": "Pozostałe Jaguar",
        "condition": "Nieuszkodzony",
        "country_origin": "Niemcy",
    },
    {
        "clasfieds_id": 875961301,
        "title": "Nissan X-Trail NISSAN X Trail ROGUE *2.5b *2019 *Automat *4x4 *LIFT *Jak NOWY *LED",
        "description": "NISSAN X-Trail / ROGUE benzyna AUTOMAT 4X4 177KM rok prod 2019 Po LIFTINGU. Przebieg tylko 37 700km!!!<br /> <br /> Samochód w idealnej kondycji, AUTO JAK NOWE. Auto w środku idealne nic nie zniszczone. Tapicerka idealna. Silnik, skrzynia, zawieszenie jak nowe. Auto sprowadzone do Polski w 2022 z USA, przebieg 37700 km.<br /> Na wyposażeniu m.in.:<br /> *automat<br /> *lampy LED (światła dzienne)<br /> *kamery cofania<br /> *NAWIGACJA (Android Auto, CarPlay)<br /> *elektryczne szyby<br /> *Przyciemniane szyby<br /> *Koła z alufelgami 17cali<br /> *Radary<br /> *skórzana kierownica<br /> *elektrycznie lusterka<br /> *radio z dużym wyświetlaczem.<br /> *Martwe pole<br /> *elektryczna klapa<br /> i wiele innych<br /> <br /> Dla Klientów oglądających ogłoszenie na OLX w celu obejrzenie większej ilości zdjęć proszę przejść do portalu OTOMOTO<br /> <br /> Posiadam historię, oraz CARFAX.<br /> <br /> ZAREJESTROWANY I UBEZPIECZONY<br /> Auto nie wymaga żadnego wkładu finansowego! JAK NOWE!<br /> <br /> Wszelkie informacje udzielę telefonicznie.<br /> Zapraszam na oględziny i jazdę próbną.",
        "price": 81900,
        "milage": 37700,
        "model": "X-Trail",
        "condition": "Nieuszkodzony",
        "country_origin": "Stany Zjednoczone",
    },
    {
        "clasfieds_id": 896440778,
        "title": "Suzuki Grand Vitara 1ROK GWARANCJI W CENIE auto w ładnym stanie xenony itd zamiana",
        "description": "MOŻLIWOŚĆ ZOSTAWIENIA SWOJEGO AUTA W ROZLICZENIU<br />  MOŻLIWOŚĆ ZAKUPU POJAZDU NA RATY CZY TEŻ LEASING <br />  WSZYSTKIE AUTA ZAREJESTROWANIE I UBEZPIECZONE W KRAJU <br /> <br />   EWENTUALNE NAPRAWY NA GWARANCJI ODBYWAJĄ SIĘ W TWOIM MIEŚCIE LUB OKOLICY !! – NIE MUSISZ JECHAĆ DO SPRZEDAWCY !!  <br /> <br />  ADRES KOMISU : <br /> <br /> 58-100 ŚWIDNICA<br /> SŁOTWINA 62J<br /> ( WYLOT NA WAŁBRZYCH ) <br />  KUPUJĄC SAMOCHÓD DOSTAJECIE PAŃSTWO : <br /> <br />  1. * GWARANCJĘ PISEMNĄ W CENIE SAMOCHODU *  1 ROK W CENIE AUTA!!! BEZ DOPŁATY!!<br /> 2. * KOMPLET NOWYCH OPON W CENIE SAMOCHODU *<br /> 3. * RABAT PIENIĘŻNY <br /> *Możliwość wybrania jednej z trzech powyższych opcji.<br /> <br />   *** KAMERA DO KAŻDEGO KUPIONEGO SAMOCHODU GRATIS! *** <br /> <br /> Witam do sprzedania posiadam samochód marki SUZUKI GRAND VITARA AUTO W B. DOBRYM STANIE AUTOMATYCZNA SKRZYNIA XENONY DOBRZE WYPOSAZONA EWENTUALNA ZAMIANA<br /> <br /> Auto jest zarejestrowane i ubezpieczone w Polsce - posiada ważny przegląd techniczny i OC.<br /> <br /> Bazując na wieloletnim doświadczeniu ( 25 lat ) pojazd pod kątem wizualnym i technicznym jest w stanie naprawdę bardzo dobrym.<br /> <br />   Wyposażenie wystawianego pojazdu to między innymi : <br /> <br /> Wszelkie pytania proszę kierować na poniższe numery telefonów : <br />    ( PREFEROWANY KONTAKT  TELEFONICZNY LUB SMS ! ) <br /> <br />   Tel. :  <br />  Tel. :   <br />  KONTAKT W SPRAWIE INFORMACJI KREDYTOWEJ :  ,  <br /> <br />   Godziny otwarcia : <br /> <br /> Pon – Pt : 9:00 – 18:00 ( w okresie zimowym godzina zamknięcia ulega zmianie - krótszy dzień )<br /> Sobota : 10:00 – 15:00<br /> Niedziela : NIECZYNNE<br /> <br />   Gwarancja, którą państwo dostajecie ( 1 ROK NA PISMIE W CENIE AUTA ) zawiera takie podzespoły jak :  <br /> ⦁ SILNIK<br /> ⦁ MANUALNĄ SKRZYNIE BIEGÓW<br /> ⦁ PASKI/ŁAŃCUCH ROZRZĄDU<br /> ⦁ ZAWIESZENIE<br /> ⦁ OBUDOWY<br /> ⦁ SPRĘŻYNY<br /> ⦁ AMORTYZATORY<br /> ⦁ ZAWIESZENIE PNEUMATYCZNE<br /> ⦁ MECHANIZMY RÓŻNICOWE<br /> ⦁ DIAGNOSTYKA I WERYFIKACJA<br /> ⦁ WAŁ PĘDNY<br /> ⦁ KOMPUTER GŁÓWNY SILNIKA<br /> ⦁ BEZSTOPNIOWA SKRZYNIA BIEGÓW<br /> ⦁ TURBINA<br /> ⦁ MATERIAŁY EKSPLOATACYJNE PODCZAS NAPRAWY<br /> ⦁ FILTR CZĄSTEK STAŁYCH  DPF<br /> ⦁ SILNIK HYBRYDOWY<br /> <br /> Proszę o kontakt telefoniczny przed przyjazdem w celu potwierdzenia aktualności oferty.<br /> <br /> *Przy zamianie gwarancja do indywidualnej negocjacji.<br /> *Niniejsze ogłoszenie jest wyłącznie informacją handlową i nie stanowi oferty w myśl art. 66,§ 1. kodeksu cywilnego.Sprzedający nie odpowiada za ewentualne błędy lub nieaktualności ogłoszenie.Zapis ten został zawarty ze względu na możliwość drobnych ludzkich pomyłek.",
        "price": 26800,
        "milage": 210000,
        "model": "Grand Vitara",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 885353335,
        "title": "Porsche Macan PORSCHE MACAN 2,0 254KM 4X4 2018r Piękny, jasne skóry",
        "description": "Witam.<br /> Do sprzedaży<br /> PORSCHE MACAN<br /> SILNIK BENZYNOWY 2.0 O MOCY 254 KM<br /> ROK PRODUKCJI: 2018<br /> <br /> AUTOMAT <br /> AWD <br /> TEMPOMAT<br /> ŁOPATKI ZMIANY BIEGÓW<br /> PAKIET SPORT CHRONO <br /> <br /> WYBRANE ELEMENTY WYPOSAŻENIA:<br /> <br /> - 4 X EL.SZYBY<br /> - EL.LUSTERKA<br /> - KOMPUTER POKŁADOWY<br /> - CLIMATRONIC<br /> - WIELOFUNKCYJNA KIEROWNICA<br /> - ABS/ESP<br /> - ISOFIX<br /> - ALUMINIOWE FELGI <br /> -  LED<br /> - 4 x AIR BAG<br /> - WIELOFUNKCYJNA KIEROWNICA<br /> - BLUETOOTH<br /> - FABRYCZNE RADIO<br /> - CZUJNIKI PARKOWANIA PRZÓD / TYŁ<br /> - CZUJNIK ZMIRZCHU<br /> - SKÓRZANA TAPICERKA + ALCANTARA<br /> - AUTOMATYCZNIE OTWIERANA / ZAMYKANA KLAPA BAGAŻNIKA <br /> - ELEKTRYCZNIE REGULOWANE FOTELE PRZÓD<br /> - KAMERA COFANIA<br />  -POLSKIE MENU + NAWIGACJA<br /> <br /> Samochód w idealnym stanie,  zarejestrowany, ubezpieczony po wymianie oleju + filtry.<br /> Oryginalny niski przebieg tylko 78 tys. km.<br /> Pełna historia<br /> Zapraszam na jazdę próbną.<br /> tel.",
        "price": 138000,
        "milage": 78000,
        "model": "Pozostałe Porsche",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 900039263,
        "title": "Renault Kadjar 1,5 diesel",
        "description": "Oferta dotyczy samochodu osobowego RENAULT KADJAR z 2019r. Auto idealnie spełnia wymagania kierowców w klasie suv. Jest poszukiwanym modelem na rynku. Samochód wizualnie jak na zdjęciach  ( bardzo ładnie utrzymany ) Środek również czysty bez plam czy otarć . Technicznie nic nie stuka nic nie puka. Silnik pracuje równo bez żadnych zastrzeżeń. Auto prowadzi się pewnie , nie słychać, ani nie czuć oznak nadmiernego eksploatowania .Posiada moc 115 KM .Na życzenie klienta możliwość sprawdzenia auta na stacji diagnostycznej. Więcej informacji telefonicznie . Zapraszam na oględziny i jazdę próbną .",
        "price": 68900,
        "milage": 72700,
        "model": "Kadjar",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 900147673,
        "title": "Audi A3 Audi A3 8V 2.0 TFSI S tronic",
        "description": 'Dzień dobry.<br /> Przedmiotem sprzedaży jest samochód marki Audi A3 model 8V rocznik, 2017 którego jestem 2 właścicielem w Polsce. Auto w moich rękach jest od czerwca 2020r. Samochód został zakupiony z przebiegiem 9320 km. Pojazd jest sprowadzony z USA, pierwsza rejestracja dnia 27.05.2017r., w Polsce pierwsza rejestracja dnia 26.03.2018r. <br /> <br /> Dane o samochodzie:<br /> Samochód marki Audi A3, model 8V wyprodukowany w 2017 roku. Napędzany silnikiem benzynowym 2.0 TFSI o mocy 190km, z napędem na przednie koła. Za zmianę biegów odpowiada jedna z najlepszych skrzyń biegów, dwusprzęgłowa, 7-stopniowa, automatyczna skrzynia DSG S-tronic. Zapewnia niesamowite wrażenia z jazdy oraz osiągi. Dzięki dwóm sprzęgłom zmiana biegów następuje błyskawicznie bez najmniejszego szarpnięcia. Auto posiada lekkie odpryski na przednim zderzaku oraz masce. Na masce jest widoczna polakierowana już rysa (po dokładnym zbliżeniu). Pojazd na dzień zamieszczenia ogłoszenia posiada przebieg o wartości 96 085km, który jest w ciągłej eksploatacji, dlatego stan licznika może się różnić podczas oględzin. Po uruchomieniu zapłonu komputer podkładowy wyświetla błąd „Audi pre-sense”. Błąd zdiagnozowany, jako problem z aktywnym tempomatem (brak pomiaru odległości od auta poprzedzającego). Błąd nie był usuwany ani naprawiany. Tempomat sam w sobie działa prawidłowo. Samochód jest garażowany. Na zaciskach założone są nakładki "Brembo". Pod spodem są standardowe zaciski. Pojazd został sprawdzony z USA przez 1 właściciela, uszkodzony, po wypadku. W chwili zakupu od 1 właściciela stan samochodu był wzorowy, nie powodował żadnych obaw. <br /> Aktualny stan pojazdu oceniam na bardzo dobry.<br /> <br /> Najważniejsze informacje/serwisy:<br /> - Wymiana oleju silnikowego - 28.11.2023<br /> - Wymiana oleju w skrzyni biegów – 28.10.2022<br /> - Naprawa układu chłodzenia (pompa wody) - 22.03.2022<br /> - Nałożona powłoka ceramiczna marki AQUA GRAPHENE COATING Car Cosmetics - 14.05.2022.<br /> Powłoka uzupełniana, co około 6 miesięcy, ostatnie uzupełnienie luty 2024r.<br /> - Wymiana tarcz i kloców tył + końcówka drążka kierowniczego – 14.07.2023<br /> <br /> - Tapicerka oraz kierownica skórzana<br /> - Apple Car Play<br /> - KeyLess go, KeyLess Entry (możliwość otworzenia drzwi lub bagażnika po dotknięciu klamki bez konieczności wyciągania kluczyka)<br /> - Tempomat<br /> - Czujnik zmierzchu, deszczu<br /> - Światła do jazdy dziennej LED oraz reflektory bi-ksenon<br /> - Ubezpieczenie OC/AC<br /> <br /> \tPosiadam również komplet kół aluminiowych \'18 z oponami letnimi. Do dorzucenia gratis dla chętnych. Posiadam wszystkie dokumenty dot. serwisu lub naprawy pojazdu. Podczas oględzin mogę udostępnić zainteresowanemu wszystkie dokumenty. Dodatkowo na koszt zainteresowanego istnieje możliwość sprawdzenia samochodu na SKP. Wszelkie inne zapytania lub terminy oględzin proszę kierować pod numer .',
        "price": 73000,
        "milage": 96085,
        "model": "A3",
        "condition": "Nieuszkodzony",
        "country_origin": "Stany Zjednoczone",
    },
    {
        "clasfieds_id": 905063104,
        "title": "Fiat 500",
        "description": "Sprowadzony-zarejestrowany w Polsce<br /> Serwisowany- książka serwisowa, dwa oryginalne kluczyki.<br /> Wnętrze wykończone czarną podsufitką i tapicerka pół skóra,<br /> czarny dach<br /> Stan techniczny i wizualny bez zastrzeżeń.<br /> Kupujący zwolniony z opłaty skarbowej- wystawiamy fakturę VAT marża.<br /> Zapraszam do kontaktu.",
        "price": 23500,
        "milage": 115000,
        "model": "500",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 776180845,
        "title": "Jeep Grand Cherokee !Stan idealny, przegląd 13.03.2025! ZAMIENIĘ",
        "description": "Dzień dobry,<br /> Do sprzedania Jeep Grand Cherokee. Jestem właścicielem samochodu blisko trzy lata. Idealna jednostka pod instalację gazową. Przy spalaniu ok. 20 litrów gazu przejazd 100 km to ok. 60 zł. Jak na tak potężny silnik, nie jest to wysoki koszt. Bezkolizyjny stan, nie uczestniczył w żadnym zdarzeniu drogowym. Niski przebieg wynika z okazjonalnego korzystania - wycieczki, weekendowe wyjazdy. Brązowy kolor skórzanej tapicerki nadaje wnętrzu oryginalny wygląd. Auto jest bardzo utrzymane. Świeżo po przeglądzie technicznym, następne badanie dopiero 13.03.2025 r.<br /> Samochód posiada m.in.:<br /> - wentylowane tarcze hamulcowe,<br /> - skórzane, wentylowane i grzane fotele przednie,<br /> - skórzane grzane fotele tylne,<br /> - podgrzewaną kierownicę,<br /> - nagłośnienie Harman Kardon,<br /> - możliwość uruchomienia auta zdalnie pilotem,<br /> - panoramiczny dach,<br /> - hak.<br /> Klimatyzacja po serwisie. Zapraszam do oglądania.",
        "price": 178000,
        "milage": 23057,
        "model": "Grand Cherokee",
        "condition": "Nieuszkodzony",
        "country_origin": "Stany Zjednoczone",
    },
    {
        "clasfieds_id": 899989957,
        "title": "MINI Clubman Mini Clubman S",
        "description": "Samochód jest bardzo zwinny, prowadzi się pewnie, nie sprawia problemów z użytkowaniem. Wymieniono amortyzatory, klocki hamulcowe i tarcze. Wszystko działa bez zarzutu, klimatyzacja jest do nabicia. Spalanie samochodu średnio wynosi 5,5 litra na 100 km. Idealny do miasta, mieści się w każdym miejscu parkingowym. Bardzo zgrabny, dzięki dwuskrzydłowym drzwiom w bagażniku sprawnie można się do niego dostać, dłuższa trasa nie stanowi dla Mini problemu. Auto nie jest bezwypadkowe.",
        "price": 22900,
        "milage": 122650,
        "model": "Pozostałe Mini",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 799371168,
        "title": "Nissan Leaf N-Connecta 40kWh*Serwisowany w ASO*Na gwarancji fabrycznej*Idealna",
        "description": "Przed przyjazdem proszę o kontakt:<br /> Pomorski Krzysztof<br /> ☎  ☎<br /> <br /> 2018 Nissan Leaf N-Connecta 40kWh + 148KM silnik elektryczny<br /> <br /> ☑ Produkcja auta: 2018r. Pierwsza rejestracja: 05,04,2018r.<br /> ☑ Auto przygotowane do rejestracji,- klient dostaje komplet dokumentów niezbędnych do zarejestrowania auta na terytorium PL w cenie auta.<br /> ☑ Posiadamy dokumentację pochodzeniową włącznie ze zdjęciami. Auto z przejrzystą historią pochodzenia.<br /> ☑ Auto serwisowane na bieżąco w ASO NISSAN,- ostatni serwis wykonany 27,10,2022r. przy przebiegu: 73,755km.<br /> ☑ Dzięki regularnym wizytom w serwisie ASO auto wciąż posiada gwarancję fabryczną W TYM GWARANCJĘ NA AKUMULATOR!<br /> (Gwarancja na cały samochód do 24.10.2023 lub przebieg 103700 km. plus assistans holowania 27.10.2023 , za rok możliwość przedłużenia.<br /> Gwarancja na akumulator ważna do kwietnia 2026r. lub do przebiegu: 160tys. km.)<br /> ☑ Auto w najbogatszej wersji wyposażenia N-Connecta.<br /> ☑ Idealny stan techniczny i wizualny.<br /> <br /> Przed przyjazdem proszę o kontakt:<br /> Pomorski Krzysztof<br /> ☎  ☎<br /> <br /> WYPOSAŻENIE:<br /> - dostęp bez kluczykowy<br /> - pół-skórzana tapicerka<br /> - podgrzewane fotele przednie<br /> - podgrzewana tylna kanapa<br /> - podgrzewana kierownica<br /> - klimatyzacja automatyczna 2 strefowa<br /> - skórzana kierownica wielofunkcyjna z regulacją w 2 płaszczyznach<br /> - elektrycznie sterowane szyby x4<br /> - elektrycznie sterowane, składane i podgrzewane lusterka zewnętrzne<br /> - nawigacja z mapą PL i EU<br /> - Bluetooth<br /> - system kamer 360'<br /> - kamera cofania z wizualizacją trajektorii cofania<br /> - czujniki parkowania przód i tył<br /> - asystent parkowania<br /> - adaptacyjne przednie reflektory w technologii FULL LED<br /> - tempomat<br /> - asystent pasa ruchu<br /> - foto chromatyczne lusterko wsteczne<br /> - tryb jazdy ekonomicznej ECO<br /> - E-pedal<br /> - fabrycznie przyciemniane szyby z filtrem UV<br /> - mocowania fotelików dziecięcych Isofix<br /> - 8 poduszek powietrznych<br /> - ABS, ESP<br /> - immobilizer<br /> - autoalarm<br /> - aluminiowe felgi<br /> <br /> Przed przyjazdem proszę o kontakt:<br /> Pomorski Krzysztof<br /> ☎  ☎<br /> <br /> Na miejscu możliwość odbycia jazdy próbnej, wgląd w dokumentację samochodu,<br /> pomiar czujnikiem lakieru, rozmowa z osobą pomocną w finansowaniu zakupu.<br /> <br /> Prosimy o wcześniejszy kontakt przed przyjazdem w celu potwierdzenia dostępności auta.<br /> <br /> Oferujemy usługę dostarczenia auta do klienta.<br /> <br /> Możliwość zostawienia auta w rozliczeniu.<br /> <br /> Kupujący zwolniony z podatku PCC (2% wartości).",
        "price": 69900,
        "milage": 74651,
        "model": "Pozostałe Nissan",
        "condition": "Nieuszkodzony",
        "country_origin": "Dania",
    },
    {
        "clasfieds_id": 825055838,
        "title": "Suzuki Swift Suzuki Swift Sport",
        "description": 'Oferta autoryzowanego dealera samochodów nowych DODGE, RAM i Suzuki .<br /> <br /> Swift Sport <br /> -Samochód na bieżąco serwisowany w ASO Suzuki<br /> -Świetny stan techniczny <br /> -Sportowy zderzak przedni<br /> -Zderzak tylny z nakładką w kształcie dyfuzora aerodynamicznego<br /> -Spojlery progowe<br /> -Spojler dachowy<br /> -Podwójna końcówka układu wydechowego<br /> -Czarne słupki nadwozia<br /> -Reflektory LED Hi/Low<br /> -Przyciemniane szyby w tylnej części nadwozia<br /> -Elektrycznie regulowane, podgrzewane i składane lusterka zewnętrzne<br /> -Sportowe fotele przednie <br /> -Pakiet Zimowy (podgrzewane fotele przednie + nawiew na nogi pasażerów z tyłu<br /> -Interaktywny system multimedialny z ekranem dotykowym 7"<br /> -Bluetooth® z zestawem głośnomówiącym<br /> -Kamera cofania <br /> -tempomat<br /> <br /> Dokumentacja zdjęciowa uszkodzeń pojazdu - pokrywa bagażnika , zderzak ,lampa tył do wglądu , samochód naprawiony w naszym ASO <br /> <br /> Polecam',
        "price": 72000,
        "milage": 60600,
        "model": "Swift",
        "condition": "Nieuszkodzony",
        "country_origin": "Niemcy",
    },
    {
        "clasfieds_id": 893265687,
        "title": "Toyota C-HR TOYOTA C HR 2.0 HYBRID Orange Edition 28.5ookm!!! OKAZJA!",
        "description": "Stan techniczny i wizualny idealny!<br /> Przebieg 28.500km<br /> Bardzo bogata wersja wyposażenia Orange Edition.<br /> Faktura vat marża!<br /> Kupujący zwolniony z podatku pcc-3 2%<br /> <br /> TEL:",
        "price": 108900,
        "milage": 29000,
        "model": "Pozostałe Toyota",
        "condition": "Nieuszkodzony",
        "country_origin": "Niemcy",
    },
    {
        "clasfieds_id": 867326890,
        "title": "Citroën C4 Full LED Automat Klimatronik Grzane fotele",
        "description": "-Rocznik 2021<br /> -Silnik 1,2 Benzyna o mocy 130 KM<br /> -Pezebieg 28 000<br /> -Automat<br /> -Klimatronik<br /> -Komputer<br /> -Tempomat<br /> -Podgrzewane fotele<br /> -EL.Szyby<br /> -eL.Lusterka<br /> -ABS<br /> -ESP<br /> -Full LED<br /> <br /> NR pojazdu 104<br /> <br /> Auto zarejestrowane w  POLSCE !!!<br /> <br /> Możliwe sprawdzenie auta na stacji diagnostycznej lub w autoryzowanym serwisie!!!<br /> <br /> Kupujący otrzymuje komplet dokumentów potrzebnych do przerejestrowania auta!<br /> <br /> Do zakupionego auta klient otrzymuje fakturę VAT-marża i jest zwolniony z opłaty skarbowej w wysokości 2% od wartości rynkowej pojazdu.<br /> Zakupy na raty oraz w leasingu załatwiamy na miejscu lub telefonicznie bez wpłaty<br /> finansowanie do 96 miesięcy <br /> możliwość finansowania bez wpisu do dowodu rejestracyjnego<br /> bez auto casco, oraz bez ograniczenia wieku pojazdu<br /> -finansujemy zakupy pojazdów dla osób od 21-go roku życia<br /> -działalności gospodarczej<br /> -umów o pracę<br /> -rolników<br /> sprawdź już teraz czy otrzymasz kredyt lub leasing<br /> kontakt w sprawie finansowania zakupu pojazdu tel. <br /> <br /> Możliwość zakupu auta z gwarancją GetHelp<br /> <br /> Zakres GWARANCJI GetHelp:<br />     • całodobowa obsługa - przez aplikację mobilną iHelp oraz infolinię Help Center,<br />     • bezpłatny assisatnce na terenie całej Polski, bezgotówkowe naprawy w sieci warsztatów współpracujących,<br />     • pokrycie kosztów zakupu części i robocizny,<br />     • samochód zastępczy na czas naprawy,<br />     • kompleksowa obsługa przez dedykowanego konsultanta,<br />     • szybki proces likwidacji usterki,<br />     • dodatkowe zniżki na roczną polisę OC / AC,<br />     • szeroki zakres pakietów gwarancji obejmujących:<br />    <br />    <br />    ZAPRASZAMY AUTO KOMIS  PERFEKT<br />    <br />    Kontakt: <br />    ul. Kcyńska 100<br />    62-100 Wągrowiec<br />    <br />    Niniejsze ogłoszenie jest wyłącznie informacją handlową i nie stanowi oferty w myśl art. 66, § 1. Kodeksu Cywilnego. Sprzedający nie odpowiada za ewentualne błędy lub nieaktualność ogłoszenia.<br /> <br /> 44FOX-ID: 616",
        "price": 82900,
        "milage": 28000,
        "model": "C4",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 905101365,
        "title": "Ford Ranger Limited 3.2 200KM Automat",
        "description": "Ford Ranger Limited z 2015 roku silnik 3.2 200KM<br /> Skrzynia, napędy sprawne.<br /> Okazyjna cena z powodu podejrzenia zmniejszenia w przeszłości przebiegu o około 50 tys. km.<br /> Na samochód wystawiam fakturę vat-marża, bez vatu!<br /> <br /> Przegląd techniczny ważny do 29 marca 2024 roku<br /> Ubezpieczenie do 10 kwietnia 2024 roku<br /> Kupujący zwolniony z opłaty skarbowej, wystawiam fakturę Vat-marża.<br /> Wyposażenie między innymi: kamera cofania, czujniki parkowania, podgrzewane skórzane fotele, hak, klimatyzacja (sprawna), navigacja, <br /> Ostatnio wymieniane klocki hamulcowe przód, nowa chłodnica klimatyzacji.",
        "price": 64500,
        "milage": 180062,
        "model": "Ranger",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
    {
        "clasfieds_id": 902044693,
        "title": "Seat Leon 2,0TDI 184ps ST X Perience 4x4Drive Navi Full LED Bezwypadek JAK NOWY!",
        "description": 'Informacja; dla osób oglądających ogłoszenie na portalu OLX - pojazd wystawiony na OTOMOTO ( więcej zdjęć na OTOMOTO )<br /> <br /> - MOŻLIWY TRANSPORT AUTA DO KLIENTA POD DOM - 2,5ZŁ ZA 1KM !!!<br /> <br /> SEAT Leon ST X-Perience 4-Drive 4x4 2,0TDI 184ps, DSG, rok produkcji 2015, modelowo 2016r<br /> Samochód z bardzo bogatym wyposażeniem, przebieg 100% oryginalny !!!!!!!<br /> Serwisowany na bieżąco do samego końca, przebieg potwierdzony pełną historią wpisów!!!<br /> Samochód po dużym serwisie:<br /> - Kompletny rozrząd<br /> - EGR<br /> - Koło dwumasowe<br /> - Amortyzatory<br /> - Filtry<br /> - Olej<br /> <br /> Samochód posiada ważne opłaty ( badanie techniczne + polisa OC )<br /> Możliwość powrotu autem na kołach do miejsca zamieszkania.<br /> <br /> - SAMOCHÓD JEST ABSOLUTNIE BEZWYPADKOWY!!!! <br /> <br /> - SAMOCHÓD JEST PRZYGOTOWANY DO REJESTRACJI - PO OPŁATACH<br /> - SPRZEDAŻ NA PODSTAWIE FAKTURY VAT-MARŻA<br /> - KUPUJĄCY ZWOLNIONY Z OPŁATY 2% !!!<br /> <br /> Auto jest wzorowo utrzymane, wnętrze jak nowe, czyste bez przetarć,<br /> technicznie - silnik, skrzynia biegów, zawieszenie w bardzo dobrym stanie.<br /> Wizualnie również w bdb. stanie!<br /> Auto nie wymaga żadnego wkładu finansowego.<br /> <br /> Bardzo bogate wyposażenie;<br /> <br /> - 2.0TDI 184ps<br /> - Najbogatsza wersja X-Perience<br /> - Automatyczna skrzynia biegów DSG<br /> - Napęd 4x4 4-Drive<br /> - Pakiet OFFROAD<br /> - Regulowane zawieszenie DRIVE SELECT (  ECO / NORMAL / SPORT / INDIVIDUAL )<br /> - Kubełkowe fotele ST<br /> - Klimatronik dwustrefowy<br /> - Nagłośnienie DSP<br /> - Światła LED tył<br /> - Alufelgi 18"<br /> - Trójramienna skórzana kierownica ST z podcięciem<br /> - Wielofunkcyjna kierownica<br /> - Lusterka wew. / zew. fotochromatyczne<br /> - Parktronik przód / tył z wizualizacją<br /> - System Nawigacji<br /> - Bluetooth / AUX / SD / <br /> - Tempomat <br /> - Podświetlenie wnętrza LED<br /> <br /> i wiele innych...<br /> <br /> Więcej informacji udzielimy telefonicznie;',
        "price": 46900,
        "milage": 248000,
        "model": "Leon",
        "condition": "Nieuszkodzony",
        "country_origin": "Polska",
    },
]


async def _check_all_offers(offers: list):
    for offer in offers:
        await predict_suspiciousness(
            offer["clasfieds_id"],
            offer["title"],
            offer["description"],
            offer["price"],
            offer["milage"],
            offer["model"],
            offer["condition"],
            offer["country_origin"],
        )


if __name__ == "__main__":
    asyncio.run(_check_all_offers(list_of_offers))
