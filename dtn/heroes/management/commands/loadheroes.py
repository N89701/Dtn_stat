import pandas as pd
from django.core.management import BaseCommand
from heroes.models import Hero

url = (r"static\data\loadheroes.csv")
df = pd.read_csv(url)


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        heroes = []
        for i in range(108):
            heroes.append(Hero(
                name=df['name'][i],
                type=df['type'][i],
                team=df['team'][i],
                component_killer=float(df['component_killer'][i]),
                component_assistant=float(df['component_assistant'][i]),
                component_teamplayer=float(df['component_teamplayer'][i])
            ))
        Hero.objects.bulk_create(heroes)
