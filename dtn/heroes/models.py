from itertools import chain

import pandas as pd
from django.db import models
from django.db.models import Avg, Sum, signals
from django.db.models.signals import post_save
from django.dispatch import receiver
from heroes.utils import leader_index

TEAM_CHOICES = [
    ('SEN', 'Sentinel'),
    ('SCO', 'Scourge'),
]

TYPE_CHOICES = [
    ('S', 'Strenght'),
    ('A', 'Agility'),
    ('I', 'Intelligence'),
]


class Hero(models.Model):
    name = models.CharField(max_length=20)
    type = models.CharField(choices=TYPE_CHOICES, max_length=10)
    team = models.CharField(choices=TEAM_CHOICES, max_length=10)
    component_killer = models.FloatField()
    component_assistant = models.FloatField()
    component_teamplayer = models.FloatField()
    icon = models.ImageField(blank=True, upload_to='icons/')
    art = models.ImageField(blank=True, upload_to='arts/')
    games = models.IntegerField(blank=True, null=True)
    wins_percent = models.FloatField(blank=True, null=True)
    kills = models.IntegerField(blank=True, null=True)
    deaths = models.IntegerField(blank=True, null=True)
    assists = models.IntegerField(blank=True, null=True)
    leader_index = models.FloatField(blank=True, null=True)
    killer_index = models.FloatField(blank=True, null=True)
    assistant_index = models.FloatField(blank=True, null=True)
    percentile_killer = models.FloatField(blank=True, null=True)
    percentile_assistant = models.FloatField(blank=True, null=True)
    rate = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['-rate', '-wins_percent']

    def __str__(self):
        return self.name


class Appearance(models.Model):
    hero = models.ForeignKey(Hero, on_delete=models.PROTECT)
    kills = models.PositiveSmallIntegerField()
    deaths = models.PositiveSmallIntegerField()
    assists = models.PositiveSmallIntegerField()
    game = models.IntegerField(blank=True, null=True)
    leader_index = models.FloatField(blank=True, null=True)
    winner = models.BooleanField()


@receiver(post_save, sender=Appearance)
def leader_index_and_game(sender, instance, created, **kwargs):
    if int(repr(instance.pk)[-1]) == 0:
        sentinel_team = Appearance.objects.filter(
            game=instance.game,
            hero__team='SEN'
        )
        scourge_team = Appearance.objects.filter(
            game=instance.game,
            hero__team='SCO'
        )
        sentinel_kills = max(
            scourge_team.aggregate(Sum('deaths'))['deaths__sum'],
            0.5
        )
        scourge_kills = max(
            sentinel_team.aggregate(Sum('deaths'))['deaths__sum'],
            0.5
        )
        participations = chain(sentinel_team, scourge_team)
        signals.post_save.disconnect(leader_index_and_game, sender=Appearance)
        game_number = 1 + (instance.pk-1)//10
        for appearance in sentinel_team:
            appearance.leader_index = leader_index(
                appearance,
                sentinel_kills,
                scourge_kills
            )
            appearance.game = game_number
        for appearance in scourge_team:
            appearance.leader_index = leader_index(
                appearance,
                scourge_kills,
                sentinel_kills
                )
            appearance.game = game_number
        Appearance.objects.bulk_update(
            participations,
            ['leader_index', 'game']
        )
        signals.post_save.connect(leader_index_and_game, sender=Appearance)
        hero_addition(sentinel_team, scourge_team)


def hero_addition(sentinel_team, scourge_team):
    participations = chain(sentinel_team, scourge_team)
    heroes = []
    for participation in participations:
        heroes.append(participation.hero)
    heroes_queryset = Hero.objects.filter(name__in=heroes)
    appearance_queryset = Appearance.objects.filter(hero__in=heroes)
    for hero in heroes_queryset:
        hero_appearances = appearance_queryset.filter(hero=hero)
        hero.games = hero_appearances.count()
        hero.wins_percent = hero_appearances.filter(winner=True)\
            .count()/hero.games
        hero.leader_index = hero_appearances\
            .aggregate(Avg('leader_index'))['leader_index__avg']
        hero.kills = hero_appearances.aggregate(Sum('kills'))['kills__sum']
        hero.assists = hero_appearances\
            .aggregate(Sum('assists'))['assists__sum']
        hero.deaths = hero_appearances.aggregate(Sum('deaths'))['deaths__sum']
        hero.assistant_index = hero.assists * 2 / hero.games / 3
        if hero.deaths:
            hero.killer_index = ((2*(hero.kills + 0.4 * hero.assists) /
                                  hero.deaths/1.65 + hero.leader_index) / 3)
    Hero.objects.bulk_update(heroes_queryset, [
        'games',
        'wins_percent',
        'leader_index',
        'kills', 'assists',
        'deaths',
        'killer_index',
        'assistant_index'
        ])
    recount_percentiles()


def recount_percentiles():
    heroes = Hero.objects.all()
    heroes_df = pd.DataFrame(list(heroes.values(
        'name',
        'assistant_index',
        'killer_index'
        )))
    heroes_df['percentile_assistant'] = heroes_df['assistant_index']\
        .rank(pct=True)
    heroes_df['percentile_killer'] = heroes_df['killer_index'].rank(pct=True)
    for hero in heroes:
        hero.percentile_assistant = heroes_df.loc[
            heroes_df['name'] == hero.name,
            'percentile_assistant'
            ].iloc[0]
        hero.percentile_killer = heroes_df.loc[
            heroes_df['name'] == hero.name,
            'percentile_killer'
            ].iloc[0]
    Hero.objects.bulk_update(heroes, [
        'percentile_assistant',
        'percentile_killer'
        ])
    rate_heroes(heroes)


def rate_heroes(heroes):
    for hero in heroes:
        if hero.games:
            hero.rate = round(0.3 * hero.wins_percent + 0.7 * (
                hero.component_killer * hero.percentile_killer +
                hero.component_assistant * hero.percentile_assistant +
                hero.component_teamplayer * hero.wins_percent), 3)
    Hero.objects.bulk_update(heroes, ['rate'])
