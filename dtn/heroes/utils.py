def leader_index(appearance, friendly_kills, enemy_kills):
    if appearance.kills == appearance.assists == 0:
        if appearance.deaths == 0:
            own_leader_index = 1
        else:
            own_leader_index = 0.125 / appearance.deaths
    elif appearance.deaths == 0:
        own_leader_index = 1.5 * appearance.kills + 0.6 * appearance.assists
    else:
        own_leader_index = ((appearance.kills + 0.4 * appearance.assists) /
                            (1.65 * appearance.deaths))
    return enemy_kills * own_leader_index / friendly_kills