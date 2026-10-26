# Game API endpoints

The game knows these web services. They are listed in its `frontend/services.xml`; this table restates them as facts, and the file itself is not included.
They are served from the game server (`production.mlb16.online.scea.com`): port 10050, or 10051 for SSL. Paths are relative to `/`.

Status:

- **real**: the server returns real data
- **seen**: the game called it during testing; it gets an empty success reply
- blank: not seen yet, also gets an empty success reply

347 services in 97 groups: 16 real, 18 seen.

## announcement

| service | path | method | ssl | status |
|---|---|---|---|---|
| `announcement.list` | `announcements.xml` | GET |  |  |
| `announcement.list_billboard_images` | `announcements/list_billboard_images.xml` | GET |  | seen |
| `announcement.list_main_menu_images` | `announcements/list_main_menu_images.xml` | GET |  | seen |

## arena_achievements

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_achievements.view` | `arena_achievements/view.xml` | GET |  |  |
| `arena_achievements.view_patches` | `arena_achievements/view_patches.xml` | GET |  |  |

## arena_audio

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_audio.view` | `arena_audio/view.xml` | GET |  |  |

## arena_buy_stadiums

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_buy_stadiums.buy_stadium` | `arena_buy_stadiums/buy_stadium.xml` | POST |  |  |
| `arena_buy_stadiums.unlocked_stadiums` | `arena_buy_stadiums/unlocked_stadiums.xml` | GET |  |  |
| `arena_buy_stadiums.unlocked_stadiums2` | `arena_buy_stadiums/unlocked_stadiums.xml` | GET |  |  |
| `arena_buy_stadiums.view_stadiums` | `arena_buy_stadiums/view_stadiums.xml` | GET |  |  |

## arena_events

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_events.view` | `arena_events/view.xml` | GET |  |  |

## arena_game

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_game.summary` | `arena_games/summary.xml` | GET |  |  |
| `arena_game.details` | `arena_games/details.xml` | GET |  |  |
| `arena_game.extra_innings` | `arena_games/extra_innings.xml` | GET |  |  |

## arena_gauntlet

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_gauntlet.pay_gauntlet` | `arena_gauntlets/pay_gauntlet.xml` | POST |  |  |
| `arena_gauntlet.get_gauntlet_price` | `arena_gauntlets/get_price.xml` | GET |  |  |

## arena_hall_of_fame

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_hall_of_fame.view` | `arena_hall_of_fames/view.xml` | GET |  |  |

## arena_home

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_home.panels` | `arena_home/panels.xml` | GET |  |  |

## arena_lineup

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_lineup.view` | `arena_lineups/view.xml` | GET |  |  |
| `arena_lineup.swap_defensive_position` | `arena_lineups/swap_defensive_position.xml` | POST |  |  |
| `arena_lineup.assign_player` | `arena_lineups/assign_player.xml` | POST |  |  |

## arena_matchups

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_matchups.list` | `arena_matchups/list.xml` | GET |  |  |

## arena_pitching_rotation

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_pitching_rotation.view` | `arena_pitching_rotations/view.xml` | GET |  |  |
| `arena_pitching_rotation.assign_player` | `arena_pitching_rotations/assign_player.xml` | POST |  |  |

## arena_player

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_player.activate` | `arena_players/activate.xml` | POST |  |  |
| `arena_player.create_dd_player` | `arena_players/create_dd_player.xml` | POST |  |  |
| `arena_player.create_picks` | `arena_players/create_picks.xml` | GET |  |  |
| `arena_player.feed` | `arena_players/feed.xml` | POST |  |  |
| `arena_player.feed_cards` | `arena_players/feed_cards.xml` | GET |  |  |
| `arena_player.equip_item` | `arena_players/equip_item.xml` | POST |  |  |
| `arena_player.unequip_item` | `arena_players/unequip_item.xml` | POST |  |  |
| `arena_player.view` | `arena_players/view.xml` | GET |  |  |
| `arena_player.view_card` | `arena_players/view_card.xml` | GET |  |  |
| `arena_player.view_items` | `arena_players/view_items.xml` | GET |  |  |
| `arena_player.view_roster` | `arena_players/view_roster.xml` | GET |  |  |
| `arena_player.release` | `arena_players/release.xml` | POST |  |  |
| `arena_player.update_stats` | `arena_players/update_stats.xml` | POST |  |  |
| `arena_player.update_active_roster` | `arena_players/update_active_roster.xml` | POST |  |  |
| `arena_player.update_batting_lineups` | `arena_players/update_batting_lineups.xml` | POST |  |  |
| `arena_player.update_pitching_rotations` | `arena_players/update_pitching_rotations.xml` | POST |  |  |
| `arena_player.update_appearances` | `arena_players/update_appearances.xml` | POST |  |  |

## arena_player_stats

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_player_stats.view` | `arena_players/view_stats.xml` | GET |  |  |

## arena_player_training

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_player_training.execute` | `arena_player_training/execute.xml` | POST |  |  |
| `arena_player_training.view_pitches` | `arena_player_training/view_pitches.xml` | GET |  |  |
| `arena_player_training.view_training_info` | `arena_player_training/view_training_info.xml` | GET |  |  |
| `arena_player_training.view_players` | `arena_player_training/view_players.xml` | GET |  |  |
| `arena_player_training.add_pitch` | `arena_player_trainings/add_pitch.xml` | POST |  |  |

## arena_quests

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_quests.attack_empty` | `arena_quests/attack_empty.xml` | POST |  |  |
| `arena_quests.challenge_team_view` | `arena_quests/challenge_team_view.xml` | GET |  |  |
| `arena_quests.def_cards` | `arena_quests/def_cards.xml` | GET |  |  |
| `arena_quests.def_pick` | `arena_quests/def_pick.xml` | POST |  |  |
| `arena_quests.do_sim` | `arena_quests/do_sim.xml` | POST |  |  |
| `arena_quests.fight` | `arena_quests/fight.xml` | POST |  |  |
| `arena_quests.get_connected_capital` | `arena_quests/get_connected_capital.xml` | GET |  |  |
| `arena_quests.get_connected_terr` | `arena_quests/get_connected_terr.xml` | GET |  |  |
| `arena_quests.move` | `arena_quests/move.xml` | POST |  |  |
| `arena_quests.reinforce` | `arena_quests/reinforce.xml` | POST |  |  |
| `arena_quests.restart` | `arena_quests/restart.xml` | POST |  |  |
| `arena_quests.skip_phase` | `arena_quests/skip_phase.xml` | POST |  |  |
| `arena_quests.steal_fans_view` | `arena_quests/steal_fans_view.xml` | GET |  |  |
| `arena_quests.sim` | `arena_quests/sim.xml` | POST |  |  |
| `arena_quests.view` | `arena_quests/view.xml` | GET |  |  |

## arena_records

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_records.view` | `arena_records/view.xml` | GET |  |  |

## arena_squad

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_squad.generate_lineup` | `arena_squads/generate_lineup.xml` | GET |  |  |
| `arena_squad.view_inventory` | `arena_squads/view_inventory.xml` | GET |  |  |
| `arena_squad.view_picks` | `arena_squads/view_picks.xml` | GET |  |  |
| `arena_squad.pick_card` | `arena_squads/pick_card.xml` | GET |  |  |
| `arena_squad.view_lineup` | `arena_squads/view_lineup.xml` | GET |  |  |
| `arena_squad.assign_player` | `arena_squads/assign_player.xml` | POST |  |  |
| `arena_squad.swap_player` | `arena_squads/swap_player.xml` | POST |  |  |
| `arena_squad.swap_position` | `arena_squads/swap_position.xml` | POST |  |  |
| `arena_squad.view_rewards` | `arena_squads/view_rewards.xml` | GET |  |  |
| `arena_squad.delete_gauntlet` | `arena_squads/delete_gauntlet.xml` | GET |  |  |

## arena_team

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_team.validate_first_page` | `arena_teams/validate_first_page.xml` | POST |  |  |
| `arena_team.create` | `arena_teams/create.xml` | POST |  |  |
| `arena_team.clear` | `arena_teams/clear.xml` | POST |  |  |
| `arena_team.destroy` | `arena_teams/:id/destroy.xml` | POST |  |  |
| `arena_team.find_xi_teams` | `arena_teams/find_xi_teams.xml` | GET |  |  |
| `arena_team.overview` | `arena_teams/overview.xml` | GET |  |  |
| `arena_team.upload_creation` | `arena_teams/upload_creation.xml` | POST |  |  |
| `arena_team.edit_team` | `arena_teams/edit_team.xml` | POST |  |  |
| `arena_team.view` | `arena_teams/view.xml` | GET |  |  |
| `arena_team.view_budget` | `arena_teams/view_budget.xml` | GET |  |  |
| `arena_team.view_by_team` | `arena_teams/view_by_team_id.xml` | GET |  |  |
| `arena_team.update_uniform` | `arena_teams/update_uniform.xml` | POST |  |  |
| `arena_team.view_friend_challenge` | `arena_teams/view_friend_challenge.xml` | GET |  |  |
| `arena_team.view_player` | `arena_teams/view_player.xml` | GET |  |  |
| `arena_team.view_uniform` | `arena_teams/view_uniform.xml` | GET |  |  |

## arena_team_season

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_team_season.view` | `arena_team_seasons/view.xml` | GET |  |  |
| `arena_team_season.last_season` | `arena_team_seasons/last_season.xml` | GET |  |  |

## arena_team_stats

| service | path | method | ssl | status |
|---|---|---|---|---|
| `arena_team_stats.view` | `arena_teams/view_stats.xml` | GET |  |  |

## cloud_save

| service | path | method | ssl | status |
|---|---|---|---|---|
| `cloud_save.list` | `cloud_saves/list.xml` | GET |  |  |
| `cloud_save.create` | `cloud_saves/create.xml` | POST |  |  |
| `cloud_save.destroy` | `cloud_saves/destroy.xml` | POST |  |  |

## challenge

| service | path | method | ssl | status |
|---|---|---|---|---|
| `challenge.current` | `challenges/current.xml` | GET |  |  |
| `challenge.post_stats` | `challenges/:id/post_stats.xml` | POST | yes |  |
| `challenge.view_leaderboard` | `challenges/view_leaderboard.xml` | GET |  |  |

## content_update

| service | path | method | ssl | status |
|---|---|---|---|---|
| `content_update.latest` | `content_updates/latest.xml` | GET |  | seen |
| `content_update.latest_retirement` | `content_updates/latest.xml` | GET |  | seen |

## document

| service | path | method | ssl | status |
|---|---|---|---|---|
| `document.list` | `documents/list.xml` | GET |  |  |
| `document.show` | `documents/show.xml` | GET |  |  |
| `document.view_by_title` | `documents/view_by_title.xml` | GET |  |  |

## events

| service | path | method | ssl | status |
|---|---|---|---|---|
| `events.open_events` | `events/open_events.xml` | GET |  |  |
| `events.overview` | `events/overview.xml` | GET |  |  |

## faction

| service | path | method | ssl | status |
|---|---|---|---|---|
| `faction.view` | `factions/view.xml` | GET |  |  |
| `faction.view_store` | `factions/view_store.xml` | GET |  |  |
| `faction.purchase_product` | `factions/purchase_product.xml` | POST |  |  |

## game_option

| service | path | method | ssl | status |
|---|---|---|---|---|
| `game_option.view` | `game_options/view.xml` | GET |  |  |

## hrd

| service | path | method | ssl | status |
|---|---|---|---|---|
| `hrd.post_stats` | `hrd_stats/update_stats.xml` | POST | yes | seen |
| `hrd.view_stats` | `hrd_stats/view_stats.xml` | GET |  |  |
| `hrd.view_stats_friends` | `hrd_stats/view_stats_friends.xml` | POST |  |  |
| `hrd.my_stats` | `hrd_stats/my_stats.xml` | GET |  | seen |

## high_priority_news_updates

| service | path | method | ssl | status |
|---|---|---|---|---|
| `high_priority_news_updates.view` | `high_priority_news_updates/view.xml` | GET |  | seen |

## inventory

| service | path | method | ssl | status |
|---|---|---|---|---|
| `inventory.check_for_rewards` | `inventories/check_for_rewards.xml` | GET |  | seen |
| `inventory.open_pack` | `inventories/open_pack.xml` | POST |  |  |
| `inventory.quick_sell` | `inventories/quick_sell.xml` | POST |  |  |
| `inventory.view` | `inventories/view.xml` | GET |  | seen |
| `inventory.view2` | `inventories/view.xml` | GET |  | seen |
| `inventory.view_collection` | `inventories/view_collection.xml` | GET |  |  |
| `inventory.view_packs` | `inventories/view_packs.xml` | GET |  |  |

## item

| service | path | method | ssl | status |
|---|---|---|---|---|
| `item.view_player` | `items/view_player.xml` | GET |  |  |

## leaderboard

| service | path | method | ssl | status |
|---|---|---|---|---|
| `leaderboard.friends_view` | `leaderboards/friends_view.xml` | GET |  |  |
| `leaderboard.view` | `leaderboards/view.xml` | GET |  |  |
| `leaderboard.view_arena_teams` | `leaderboards/view_arena_teams.xml` | GET |  |  |
| `leaderboard.view_arena_players` | `leaderboards/view_arena_players.xml` | GET |  |  |

## league

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league.advance_season` | `leagues/advance_season.xml` | POST |  |  |
| `league.advance_season_options` | `leagues/advance_season_options.xml` | GET |  |  |
| `league.advance_series` | `leagues/advance_series.xml` | POST |  |  |
| `league.available_teams` | `leagues/available_teams.xml` | GET |  |  |
| `league.create` | `leagues/create.xml` | POST |  |  |
| `league.details` | `leagues/details.xml` | GET |  |  |
| `league.edit_division_name` | `leagues/edit_division_name.xml` | POST |  |  |
| `league.edit_league_name` | `leagues/edit_league_name.xml` | POST |  |  |
| `league.history` | `leagues/history.xml` | GET |  |  |
| `league.list` | `leagues/list.xml` | GET |  |  |
| `league.mine` | `leagues/mine.xml` | GET |  |  |
| `league.reassign_commissioner` | `leagues/reassign_commissioner.xml` | POST |  |  |
| `league.round_status` | `leagues/round_status.xml` | GET |  |  |
| `league.start` | `leagues/start.xml` | POST |  |  |
| `league.upload_roster` | `leagues/upload_roster.xml` | POST |  |  |
| `league.view_create` | `leagues/view_create.xml` | GET |  |  |
| `league.view_settings` | `leagues/view_settings.xml` | GET |  |  |

## league_advancement_status

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_advancement_status.view` | `league_advancement_statuses/view.xml` | GET |  |  |
| `league_advancement_status.update` | `league_advancement_statuses/update.xml` | POST |  |  |

## league_award

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_award.view` | `league_awards/view.xml` | GET |  |  |

## league_batting_lineup

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_batting_lineup.update_all` | `league_batting_lineups/update_all.xml` | POST |  |  |
| `league_batting_lineup.view_lineups` | `league_batting_lineups/view_lineups.xml` | GET |  |  |

## league_bulletin_board

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_bulletin_board.create` | `league_bulletin_boards/create.xml` | POST |  |  |
| `league_bulletin_board.view` | `league_bulletin_boards/view.xml` | GET |  |  |
| `league_bulletin_board.destroy` | `league_bulletin_boards/destroy.xml` | POST |  |  |

## league_coach

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_coach.view` | `league_coaches/view.xml` | GET |  |  |
| `league_coach.hire` | `league_coaches/hire.xml` | POST |  |  |
| `league_coach.fire` | `league_coaches/fire.xml` | POST |  |  |

## league_contract

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_contract.view` | `league_contracts/view.xml` | GET |  |  |
| `league_contract.view_player` | `league_contracts/view_player.xml` | GET |  |  |
| `league_contract.offer` | `league_contracts/offer.xml` | POST |  |  |
| `league_contract.withdraw` | `league_contracts/withdraw.xml` | POST |  |  |

## league_commissioner_rating

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_commissioner_rating.create` | `league_commissioner_ratings/create.xml` | POST |  |  |

## league_division

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_division.view_standing` | `league_divisions/view_standing.xml` | GET |  |  |

## league_draft

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_draft.check_status` | `league_drafts/check_status.xml` | GET |  |  |
| `league_draft.draft_player` | `league_drafts/draft_player.xml` | POST |  |  |
| `league_draft.list` | `league_drafts/list.xml` | GET |  |  |
| `league_draft.list_amateurs` | `league_drafts/list_amateurs.xml` | GET |  |  |
| `league_draft.queue_add_player` | `league_drafts/queue_add_player.xml` | POST |  |  |
| `league_draft.queue_remove_player` | `league_drafts/queue_remove_player.xml` | POST |  |  |
| `league_draft.queue_swap_players` | `league_drafts/queue_swap_players.xml` | POST |  |  |
| `league_draft.set_auto_draft` | `league_drafts/set_auto_draft.xml` | POST |  |  |
| `league_draft.view` | `league_drafts/view.xml` | GET |  |  |

## league_event

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_event.view` | `league_events/view.xml` | GET |  |  |

## league_free_agent_pool

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_free_agent_pool.list` | `league_free_agent_pools/list.xml` | GET |  |  |
| `league_free_agent_pool.release` | `league_free_agent_pools/release.xml` | POST |  |  |
| `league_free_agent_pool.sign` | `league_free_agent_pools/sign.xml` | POST |  |  |

## league_game

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_game.cancel` | `league_games/cancel.xml` | POST |  |  |
| `league_game.details` | `league_games/details.xml` | GET |  |  |
| `league_game.list` | `league_games/list.xml` | GET |  |  |
| `league_game.next_game` | `league_games/next_game.xml` | GET |  |  |
| `league_game.reset` | `league_games/reset.xml` | POST |  |  |
| `league_game.resolve` | `league_games/resolve.xml` | POST |  |  |
| `league_game.sim_game` | `league_games/sim_game.xml` | POST |  |  |
| `league_game.start` | `league_games/start.xml` | POST |  |  |

## league_hof

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_hof.view` | `league_hofs/view.xml` | GET |  |  |

## league_invite

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_invite.create` | `league_invites/create.xml` | POST |  |  |
| `league_invite.league_view` | `league_invites/league_view.xml` | GET |  |  |
| `league_invite.reject` | `league_invites/reject.xml` | POST |  |  |
| `league_invite.revoke` | `league_invites/revoke.xml` | POST |  |  |
| `league_invite.view` | `league_invites/view.xml` | GET |  |  |

## league_leader

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_leader.view` | `league_leaders/view.xml` | GET |  |  |

## league_lineup

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_lineup.view` | `league_lineups/view.xml` | GET |  |  |
| `league_lineup.swap_defensive_position` | `league_lineups/swap_defensive_position.xml` | POST |  |  |
| `league_lineup.assign_player` | `league_lineups/assign_player.xml` | POST |  |  |

## league_panel

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_panel.view` | `league_panels/view.xml` | GET |  |  |

## league_pitching_rotation

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_pitching_rotation.view` | `league_pitching_rotations/view.xml` | GET |  |  |
| `league_pitching_rotation.assign_player` | `league_pitching_rotations/assign_player.xml` | POST |  |  |

## league_player

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_player.change_division` | `league_players/change_division.xml` | POST |  |  |
| `league_player.release` | `league_players/release.xml` | POST |  |  |
| `league_player.update_batting_lineups` | `league_players/update_batting_lineups.xml` | POST |  |  |
| `league_player.update_pitching_rotations` | `league_players/update_pitching_rotations.xml` | POST |  |  |
| `league_player.view` | `league_players/view.xml` | GET |  |  |
| `league_player.view_roster` | `league_players/view_roster.xml` | GET |  |  |
| `league_player.view_injuries` | `league_players/view_injuries.xml` | GET |  |  |
| `league_player.view_card` | `league_players/view_card.xml` | GET |  |  |

## league_player_stat

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_player_stat.view` | `league_player_stats/view.xml` | GET |  |  |
| `league_player_stat.update` | `league_player_stats/update.xml` | POST |  |  |

## league_playoff

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_playoff.view` | `league_playoffs/view.xml` | GET |  |  |

## league_retirement

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_retirement.view` | `league_retirements/view.xml` | GET |  |  |

## league_role

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_role.set_roles` | `league_roles/set_roles.xml` | POST |  |  |
| `league_role.list` | `league_roles/list.xml` | GET |  |  |

## league_scout

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_scout.view_players` | `league_scouts/view_players.xml` | GET |  |  |
| `league_scout.view_prospect_info` | `league_scouts/view_prospect_info.xml` | GET |  |  |
| `league_scout.change_orders` | `league_scouts/change_orders.xml` | POST |  |  |
| `league_scout.view` | `league_scouts/view.xml` | GET |  |  |
| `league_scout.hire` | `league_scouts/hire.xml` | POST |  |  |
| `league_scout.fire` | `league_scouts/fire.xml` | POST |  |  |

## league_setting

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_setting.view` | `league_settings/view.xml` | GET |  |  |
| `league_setting.view_game_options` | `league_settings/view_game_options.xml` | GET |  |  |
| `league_setting.update` | `league_settings/update.xml` | GET |  |  |

## league_schedule

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_schedule.view` | `league_schedules/view.xml` | GET |  |  |
| `league_schedule.preview` | `league_schedules/preview.xml` | GET |  |  |

## league_slider

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_slider.download` | `league_sliders/download.xml` | GET |  |  |
| `league_slider.update` | `league_sliders/update.xml` | POST |  |  |
| `league_slider.view` | `league_sliders/view.xml` | GET |  |  |

## league_team

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_team.assign_slot` | `league_teams/assign_slot.xml` | POST |  |  |
| `league_team.drop` | `league_teams/drop.xml` | POST |  |  |
| `league_team.fix_rotation_and_lineups` | `league_teams/fix_rotation_and_lineups.xml` | POST |  |  |
| `league_team.fix_roster` | `league_teams/fix_roster.xml` | POST |  |  |
| `league_team.join` | `league_teams/join.xml` | POST |  |  |
| `league_team.list` | `league_teams/list.xml` | GET |  |  |
| `league_team.swap_slots` | `league_teams/swap_slots.xml` | POST |  |  |
| `league_team.toggle_all` | `league_teams/toggle_all.xml` | POST |  |  |
| `league_team.view_users` | `league_teams/view_users.xml` | GET |  |  |
| `league_team.view` | `league_teams/view.xml` | GET |  |  |
| `league_team.view_settings` | `league_teams/view_settings.xml` | GET |  |  |
| `league_team.update_settings` | `league_teams/update_settings.xml` | POST |  |  |
| `league_team.quit` | `league_teams/quit.xml` | POST |  |  |

## league_team_ranking

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_team_ranking.view` | `league_team_rankings/view.xml` | GET |  |  |

## league_team_stat

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_team_stat.view` | `league_team_stats/view.xml` | GET |  |  |

## league_trade

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_trade.accept` | `league_trades/accept.xml` | POST |  |  |
| `league_trade.propose` | `league_trades/propose.xml` | POST |  |  |
| `league_trade.cancel` | `league_trades/cancel.xml` | POST |  |  |
| `league_trade.view` | `league_trades/view.xml` | GET |  |  |
| `league_trade.list` | `league_trades/list.xml` | GET |  |  |
| `league_trade.reject` | `league_trades/reject.xml` | POST |  |  |
| `league_trade.vote` | `league_trades/vote.xml` | POST |  |  |

## league_trade_block

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_trade_block.view` | `league_trade_blocks/view.xml` | GET |  |  |
| `league_trade_block.update_view` | `league_trade_blocks/update_view.xml` | GET |  |  |
| `league_trade_block.change_stance` | `league_trade_blocks/change_stance.xml` | POST |  |  |
| `league_trade_block.set_player_block` | `league_trade_blocks/set_player_block.xml` | POST |  |  |

## league_training

| service | path | method | ssl | status |
|---|---|---|---|---|
| `league_training.view` | `league_trainings/view.xml` | GET |  |  |
| `league_training.change_training` | `league_trainings/change_training.xml` | POST |  |  |

## live_games

| service | path | method | ssl | status |
|---|---|---|---|---|
| `live_games.arena_cpu_roster` | `live_games/arena_cpu_roster.xml` | GET |  |  |
| `live_games.calendar_view` | `live_games/calendar_view.xml` | GET |  |  |
| `live_games.hotbar` | `live_games/ticker.xml` | GET |  | seen |
| `live_games.more_info` | `live_games/more_info.xml` | GET |  |  |
| `live_games.game_info` | `live_games/game_info.xml` | GET |  |  |
| `live_games.games` | `live_games/games.xml` | GET |  |  |
| `live_games.lineup` | `live_games/lineup.xml` | GET |  |  |
| `live_games.team_lineup` | `live_games/team_lineup.xml` | GET |  |  |
| `live_games.ticker` | `live_games/ticker.xml` | GET |  | seen |
| `live_games.tickers` | `live_games/ticker.xml` | GET |  | seen |

## lobby_channel

| service | path | method | ssl | status |
|---|---|---|---|---|
| `lobby_channel.list_with_my_league_rooms` | `lobby_channels/list_with_my_league_rooms.xml` | GET |  | **real** |
| `lobby_channel.show` | `lobby_channels/show.xml` | GET |  | **real** |

## lobby_channel_player

| service | path | method | ssl | status |
|---|---|---|---|---|
| `lobby_channel_player.join` | `lobby_channel_players/join_with_ping.xml` | POST |  | **real** |
| `lobby_channel_player.list` | `lobby_channel_players/list_with_ping.xml` | GET |  | **real** |
| `lobby_channel_player.quit` | `lobby_channel_players/quit.xml` | POST |  | **real** |

## marketplace

| service | path | method | ssl | status |
|---|---|---|---|---|
| `marketplace.view` | `marketplaces/view.xml` | GET |  |  |
| `marketplace.view_listing` | `marketplaces/view_listing.xml` | GET |  |  |
| `marketplace.view_my_orders` | `marketplaces/view_my_orders.xml` | GET |  |  |
| `marketplace.view_completed_orders` | `marketplaces/view_completed_orders.xml` | GET |  |  |
| `marketplace.submit_order` | `marketplaces/submit_order.xml` | POST |  |  |
| `marketplace.cancel_order` | `marketplaces/cancel_order.xml` | POST |  |  |

## mlb_login

| service | path | method | ssl | status |
|---|---|---|---|---|
| `mlb_login.login` | `mlb_logins/login.xml` | POST | yes | **real** |
| `mlb_login.post_update` | `mlb_login/post_update.xml` | POST |  | **real** |
| `mlb_login.check_daily` | `mlb_login/check_daily.xml` | GET |  | seen |

## mlb_master

| service | path | method | ssl | status |
|---|---|---|---|---|
| `mlb_master.debug_operation` | `mlb_masters/debug_operation.xml` | POST |  |  |

## mlb_game

| service | path | method | ssl | status |
|---|---|---|---|---|
| `mlb_game.create` | `mlb_games/create.xml` | POST | yes | seen |
| `mlb_game.start` | `mlb_games/start.xml` | POST | yes | **real** |
| `mlb_game.view` | `mlb_games/view.xml` | GET |  | seen |
| `mlb_game.view_details` | `mlb_games/view_details.xml` | GET |  |  |

## mlb_players

| service | path | method | ssl | status |
|---|---|---|---|---|
| `mlb_players.player_changes` | `mlb_players/player_changes.xml` | GET |  |  |
| `mlb_players.original_teams` | `mlb_players/original_teams.xml` | GET |  |  |
| `mlb_players.vscpu_values` | `mlb_players/vscpu_values.xml` | GET |  |  |

## mlb_quest

| service | path | method | ssl | status |
|---|---|---|---|---|
| `mlb_quest.view` | `mlb_quests/view.xml` | GET |  |  |
| `mlb_quest.advance` | `mlb_quests/advance.xml` | POST |  |  |
| `mlb_quest.complete` | `mlb_quests/complete.xml` | POST |  |  |

## pitcher_rotation_energy

| service | path | method | ssl | status |
|---|---|---|---|---|
| `pitcher_rotation_energy.update` | `pitcher_rotations/update.xml` | POST |  |  |
| `pitcher_rotation_energy.view` | `pitcher_rotations/view.xml` | GET |  |  |

## player_archive

| service | path | method | ssl | status |
|---|---|---|---|---|
| `player_archive.history` | `player_archives/history.xml` | GET |  |  |

## player

| service | path | method | ssl | status |
|---|---|---|---|---|
| `player.batch_lookup` | `players/batch_lookup.xml` | POST |  | **real** |
| `player.batch_lookup_for_challenge` | `players/batch_lookup.xml` | POST |  | **real** |
| `player.deserter` | `players/deserter.xml` | POST |  |  |
| `player.deserter_check` | `players/deserter_check.xml` | GET |  |  |
| `player.hotbar_lookup_for_challenge` | `players/batch_lookup.xml` | POST |  | **real** |
| `player.info` | `players/info2.xml` | GET |  | **real** |
| `player.info_for_challenge` | `players/info2.xml` | GET |  | **real** |
| `player.vote` | `players/vote.xml` | POST |  |  |

## player_complaint

| service | path | method | ssl | status |
|---|---|---|---|---|
| `player_complaint.create` | `player_complaints/create.xml` | POST |  |  |
| `player_complaint.reasons` | `player_complaints/reasons.xml` | GET |  |  |

## player_creation

| service | path | method | ssl | status |
|---|---|---|---|---|
| `player_creation.create` | `player_creations/create.xml` | POST |  |  |
| `player_creation.destroy` | `player_creations/destroy.xml` | POST |  |  |
| `player_creation.download` | `player_creations/download.xml` | POST |  |  |
| `player_creation.list` | `player_creations/list.xml` | GET |  |  |

## player_creation_rating

| service | path | method | ssl | status |
|---|---|---|---|---|
| `player_creation_rating.create` | `player_creation_ratings/create.xml` | POST |  |  |

## player_profile

| service | path | method | ssl | status |
|---|---|---|---|---|
| `player_profile.update` | `player_profile/mlb_update.xml` | POST |  |  |
| `player_profile.view` | `player_profile/mlb_view.xml` | GET |  |  |

## playnow_settings

| service | path | method | ssl | status |
|---|---|---|---|---|
| `playnow_settings.view` | `playnow_settings/view.xml` | GET |  |  |

## policy

| service | path | method | ssl | status |
|---|---|---|---|---|
| `policy.accept` | `policies/:id/accept.xml` | POST |  |  |
| `policy.view` | `policies/view.xml` | GET |  |  |

## rss_item

| service | path | method | ssl | status |
|---|---|---|---|---|
| `rss_item.show` | `rss_items/show.xml` | GET |  |  |
| `rss_item.top_headlines` | `rss_items/top_headlines.xml` | GET |  |  |
| `rss_item.hotbar_top_headlines` | `rss_items/top_headlines.xml` | GET |  |  |
| `rss_item.top_headlines_by_provider` | `rss_items/top_headlines_by_provider.xml` | GET |  |  |

## rtts

| service | path | method | ssl | status |
|---|---|---|---|---|
| `rtts.view_stats` | `rtts/view_stats.xml` | GET |  |  |
| `rtts.update_stats` | `rtts/update_stats.xml` | POST | yes |  |

## server

| service | path | method | ssl | status |
|---|---|---|---|---|
| `server.get_ping_server` | `servers/get_ping_server.xml` | GET |  | seen |
| `server.select` | `servers/select.xml` | POST |  | **real** |

## session

| service | path | method | ssl | status |
|---|---|---|---|---|
| `session.ping` | `session/ping.xml` | POST |  | **real** |

## show_shop_product

| service | path | method | ssl | status |
|---|---|---|---|---|
| `show_shop_product.view` | `show_shop_products/view.xml` | GET | yes |  |
| `show_shop_product.buy` | `show_shop_products/buy.xml` | POST | yes |  |
| `show_shop_product.view_psn` | `show_shop_products/view_psn.xml` | GET | yes |  |
| `show_shop_product.redeem` | `show_shop_products/redeem.xml` | POST | yes |  |
| `show_shop_product.purchase_complete` | `show_shop_products/purchase_complete.xml` | POST | yes |  |

## sub_leaderboard

| service | path | method | ssl | status |
|---|---|---|---|---|
| `sub_leaderboard.view` | `sub_leaderboards/view.xml` | GET |  |  |
| `sub_leaderboard.friends_view` | `sub_leaderboards/friends_view.xml` | GET |  |  |

## ticker

| service | path | method | ssl | status |
|---|---|---|---|---|
| `ticker.view` | `tickers/view.xml` | GET |  |  |
| `ticker.view_by_game` | `tickers/view_by_game.xml` | GET |  |  |
| `ticker.view_compact` | `tickers/view_compact.xml` | GET |  |  |

## trophy

| service | path | method | ssl | status |
|---|---|---|---|---|
| `trophy.list` | `trophies.xml` | GET |  |  |

## twitter

| service | path | method | ssl | status |
|---|---|---|---|---|
| `twitter.team_feeds` | `twitter_feeds/team_feeds.xml` | GET |  |  |
| `twitter.player_feeds` | `twitter_feeds/player_feeds.xml` | GET |  |  |

## uc_challenge

| service | path | method | ssl | status |
|---|---|---|---|---|
| `uc_challenge.browse_options` | `uc_challenge/browse_options.xml` | GET |  |  |
| `uc_challenge.check_fees` | `uc_challenge/check_fees.xml` | GET |  |  |
| `uc_challenge.create` | `uc_challenge/create.xml` | POST |  |  |
| `uc_challenge.destroy` | `uc_challenge/destroy.xml` | POST |  |  |
| `uc_challenge.download` | `uc_challenge/download.xml` | POST |  |  |
| `uc_challenge.flag` | `uc_challenge/flag.xml` | POST |  |  |
| `uc_challenge.get_leaderboard_payouts` | `` | GET |  |  |
| `uc_challenge.list` | `uc_challenge/list.xml` | GET |  |  |
| `uc_challenge.tag_list` | `uc_challenge/tag_list.xml` | GET |  |  |
| `uc_challenge.start` | `uc_challenge/start.xml` | POST |  |  |
| `uc_challenge.completed` | `uc_challenge/completed.xml` | POST |  |  |
| `uc_challenge.update_stats` | `uc_challenge/update_stats.xml` | POST |  |  |
| `uc_challenge.rate` | `uc_challenge/rate.xml` | POST |  |  |
| `uc_challenge.view_stats` | `uc_challenge/view_stats.xml` | GET |  |  |

## uc_challenge_rating

| service | path | method | ssl | status |
|---|---|---|---|---|
| `uc_challenge_rating.create` | `uc_challenge_ratings/create.xml` | POST |  |  |

## universal_profile

| service | path | method | ssl | status |
|---|---|---|---|---|
| `universal_profile.update` | `universal_profiles/update.xml` | POST | yes | **real** |
| `universal_profile.update_lite` | `universal_profiles/update_lite.xml` | POST | yes |  |
| `universal_profile.view` | `universal_profiles/view.xml` | GET |  | seen |
