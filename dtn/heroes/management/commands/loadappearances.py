import pandas as pd
from django.core.management import BaseCommand
from heroes.models import Appearance

url = (r"static\data\loadappearances.csv")
df = pd.read_csv(url)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for i in range(2050):
            hero = df['hero'][i]
            winner = df['winner'][i]
            kills = df['kills'][i]
            deaths = df['deaths'][i]
            assists = df['assists'][i]
            Appearance.objects.create(
                hero_id=hero,
                winner=winner,
                kills=kills,
                deaths=deaths,
                assists=assists,
            )
