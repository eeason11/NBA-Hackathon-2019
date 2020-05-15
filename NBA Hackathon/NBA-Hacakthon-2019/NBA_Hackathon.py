import pandas as pd
import numpy as np
import os

MAX_EVENT_INDEX = 37889

'''These are indices for various features of the three provided data sets 
   (since the dataframes are converted to ndarrays for efficiency purposes '''
GAME_ID_INDEX = 0
PERIOD_INDEX = 1
STATUS_INDEX = 4
PLAYER_ID_INDEX = 2
TEAM_ID_INDEX = 3
TEAM_ID_2_INDEX = 10
PERIOD_INDEX_PBP = 3
MSG_TYPE_INDEX = 2
ACTION_TYPE_INDEX = 6
PERSON1_INDEX = 11
OPTION1_INDEX = 7
PERSON2_INDEX = 12

'''These are arrays of action types for various categories of events'''
tech_fouls = [11, 12, 13, 16, 18, 19, 21, 25, 30] # technical fouls
flag_fouls = [14, 15] # flagrant fouls
tech_fts = [16, 21, 22] # technical foul FTs
flag_fts = [18, 19, 20, 27, 28, 29] # flagrant foul FTs
flag_cont_fts = [18, 27, 28] # flagrant foul FTs that are not the last FT in that particular series of FTs
reg_cont_fts = [11, 13, 14, 25] # regular FTs that are not the last FT in that particular series of FTs
ft_end = [10, 12, 15, 17, 19, 20, 26, 29] # all FTs that are the last FT in that particular series of FTs
vio_ch_poss = [4, 5] # violations that can result in a change of possession

class Player:
    off_poss = 0
    def_poss = 0
    team_pts = 0
    opp_pts = 0
    in_game = False
    def __init__(self, pid, gid, tid):
        self.pid = pid # player_id
        self.gid = gid # game_id
        self.tid = tid # team_id

ec_filepath = os.path.join('C:/Users/ethan/NBA Hackathon', 'Event_Codes.csv')
event_codes_df = pd.read_csv(ec_filepath)
gl_filepath = os.path.join('C:/Users/ethan/NBA Hackathon', 'Game_Lineup.csv')
game_lineup_df = pd.read_csv(gl_filepath)
pbp_filepath = os.path.join('C:/Users/ethan/NBA Hackathon', 'Play_by_Play.csv')
play_by_play_df = pd.read_csv(pbp_filepath)

play_by_play_df = play_by_play_df.sort_values(by=['Game_id', 'Period', 'PC_Time', 'WC_Time', 'Event_Num'], 
                                              ascending=[True, True, False, True, True])
print(play_by_play_df) 

ec_arr = event_codes_df.to_numpy()
gl_arr = game_lineup_df.to_numpy()
pbp_arr = play_by_play_df.to_numpy()

prev_gid = ""
prev_q = 0
teams = [] # tracks which two teams are in a game
possession = "" # tracks which team in a certain game for a certain event is in possession
games_dict = {} # keys are games, values are dictionaries of player objects (player_ratings)
player_ratings= {} # keys are pids, values are player objects
first_fourth = "" # team that wins the tip
sec_third = "" # team that does not win the tip

def find_index(gid): # finds the index of a game in the game lineup ndarray
    for i in range(len(gl_arr)):
        if gl_arr[i][GAME_ID_INDEX] == gid:
            return i

def sub_all(): # changes all players in player ratings's status to out of game
    for player in player_ratings.values() :
        player.in_game = False
        
def quarter_lineups(gid, q): # updates new quarter lineups accordingly
    sub_all()
    g_index = find_index(gid)
    q_index = 0
    for i in range(g_index, len(gl_arr)):
        if(gl_arr[i][PERIOD_INDEX] == q):
            q_index = i
            break
    for i in range(q_index, q_index + 10):
        player_ratings[gl_arr[i][PLAYER_ID_INDEX]].in_game = True    

for i in range(MAX_EVENT_INDEX):    # iterates over every game event
    print(i)
    curr_gid = pbp_arr[i][GAME_ID_INDEX]
    curr_q = pbp_arr[i][PERIOD_INDEX_PBP]
    if (curr_gid == prev_gid):
        if (curr_q != prev_q): # new quarter
            quarter_lineups(curr_gid, curr_q)
            if curr_q == 1 or curr_q == 4:
                possession = first_fourth
            elif curr_q == 2 or curr_q == 3:
                possession = sec_third 
    else: # new game
        # store game-level objects
        if (prev_gid != ""):
            games_dict[prev_gid] = player_ratings
        
        # clears all game-level objects
        player_ratings = {}
        possession = ""
        teams = []
        first_fourth = ""
        sec_third = ""
        curr_q = 0
        
        # creates new dict of player objects (player_ratings) for the next game
        games_dict[curr_gid] = {}
        game_index = find_index(curr_gid)
        player_add_index = game_index
        while(gl_arr[player_add_index][PERIOD_INDEX] == 0):
            if gl_arr[player_add_index][STATUS_INDEX] == 'A':
                team = gl_arr[player_add_index][TEAM_ID_INDEX]
                if team not in teams:
                    teams.append(team)
                p = Player(gl_arr[player_add_index][PLAYER_ID_INDEX], curr_gid, team)
                player_ratings[p.pid] = p
            player_add_index += 1
    
    
    msg_type = pbp_arr[i][MSG_TYPE_INDEX]
    action_type = pbp_arr[i][ACTION_TYPE_INDEX]
    points_involved = 0
    poss_change = False
    if (msg_type == 1): # made field goals
        if action_type != 0:
            possession = player_ratings[pbp_arr[i][PERSON1_INDEX]].tid
            points_involved += pbp_arr[i][OPTION1_INDEX]
            poss_change = True
        
    elif (msg_type == 6): # fouls and free throws
        if (action_type == 10 or action_type == 16): # double personal or double technicals
            player1 = pbp_arr[i][PERSON1_INDEX]
            player2 = pbp_arr[i][PERSON2_INDEX]
            player1_pts = 0
            player2_pts = 0
            num_fts = 0
            if action_type == 10:
                for n in range(i+1, i+25):
                    if num_fts == 4:
                        break
                    n_msg_type = pbp_arr[n][MSG_TYPE_INDEX]
                    n_action_type = pbp_arr[n][ACTION_TYPE_INDEX]
                    if n_msg_type == 3 and n_action_type not in flag_fts and n_action_type not in tech_fts:
                        if pbp_arr[n][PERSON1_INDEX] == player1 or pbp_arr[n][PERSON1_INDEX] == player2:
                            num_fts += 1
                            if pbp_arr[n][OPTION1_INDEX] == 1:
                                if(pbp_arr[n][PERSON1_INDEX] == player1):
                                    player1_pts += 1
                                elif(pbp_arr[n][PERSON1_INDEX] == player2):
                                    player2_pts += 1          
                    if n_msg_type == 6 and n_action_type not in tech_fouls:
                        break
            else:
                for n in range(i+1, i+25):
                    n_msg_type = pbp_arr[n][MSG_TYPE_INDEX]
                    n_action_type = pbp_arr[n][ACTION_TYPE_INDEX]
                    if n_msg_type == 3 and n_action_type in tech_fts:
                        if pbp_arr[n][PERSON1_INDEX] == player1 or pbp_arr[n][PERSON1_INDEX] == player2:
                            num_fts += 1
                            if pbp_arr[n][OPTION1_INDEX] == 1:
                                if(pbp_arr[n][PERSON1_INDEX] == player1):
                                    player1_pts += 1
                                elif(pbp_arr[n][PERSON1_INDEX] == player2):
                                    player2_pts += 1          
                    if n_msg_type == 6 and n_action_type not in tech_fouls:
                        break                
            for player in player_ratings.values():
                if player.in_game:
                    if player.tid == player_ratings[player1].tid:
                        player.team_pts += player1_pts
                        player.opp_pts += player2_pts
                    else:
                        player.team_pts += player2_pts
                        player.opp_pts += player1_pts
        elif (action_type in tech_fouls): # technical fouls
            for n in range(i+1, i+25):
                n_msg_type = pbp_arr[n][MSG_TYPE_INDEX]
                n_action_type = pbp_arr[n][ACTION_TYPE_INDEX]
                if n_msg_type == 3 and n_action_type in tech_fts:
                    made_ft = (pbp_arr[n][OPTION1_INDEX] == 1)
                    if made_ft:
                        points_involved += 1
                    if n_action_type != tech_fts[1]:
                        break
        elif (action_type in flag_fouls): # flagrant fouls
            for n in range(i+1, i+25):
                n_msg_type = pbp_arr[n][MSG_TYPE_INDEX]
                n_action_type = pbp_arr[n][ACTION_TYPE_INDEX]
                if n_msg_type == 3 and n_action_type in flag_fts:
                    if pbp_arr[n][OPTION1_INDEX] == 1:
                        points_involved += 1 
                    if n_action_type not in flag_cont_fts:
                        break
                if n_msg_type == 6 and n_action_type not in tech_fouls:
                    break                    
        else: # regular fouls
            if action_type != 0:
                for n in range(i+1, i+25):
                    n_msg_type = pbp_arr[n][MSG_TYPE_INDEX]
                    n_action_type = pbp_arr[n][ACTION_TYPE_INDEX]
                    if n_msg_type == 3 and n_action_type not in flag_fts and n_action_type not in tech_fts:
                        if pbp_arr[n][OPTION1_INDEX] == 1:
                            points_involved += 1 
                        if n_action_type not in reg_cont_fts:
                            break            
                    if n_msg_type == 6 and n_action_type not in tech_fouls:
                        break
                
    elif (msg_type == 3): # made free throws
        if action_type != 0:
            if (action_type not in tech_fts and action_type not in flag_fts) or (action_type in flag_fts and player_ratings[pbp_arr[i][PERSON1_INDEX]].tid != possession): # if the player shooting the FT is not on the team in possession
                if pbp_arr[i][OPTION1_INDEX] == 1 and action_type in ft_end:
                    poss_change = True
    
    elif (msg_type == 4): # rebounds
        if (action_type == 1 and pbp_arr[i][TEAM_ID_2_INDEX] != possession):
            poss_change = True
    
    elif (msg_type == 5): # turnovers
        player_team = pbp_arr[i][TEAM_ID_2_INDEX]
        if possession != player_team:
            possession = player_team
        if action_type != 0:
            poss_change = True
    
    elif (msg_type == 7): # violations
        if action_type in vio_ch_poss and pbp_arr[i][TEAM_ID_2_INDEX] == possession:
            poss_change = True
            
    elif (msg_type == 8): # substitutions
        player_ratings[pbp_arr[i][PERSON1_INDEX]].in_game = False
        player_ratings[pbp_arr[i][PERSON2_INDEX]].in_game = True
    
    elif (msg_type == 10): # jump ball
        win_team = pbp_arr[i][TEAM_ID_2_INDEX] # team that wins the jump
        if possession != "":
            if possession != win_team:
                poss_change = True
        else:
            possession = win_team
            first_fourth = win_team
            if teams[0] == first_fourth:
                sec_third = teams[1]
            else:
                sec_third = teams[0]
    
    elif (msg_type == 13): # end of quarter
        poss_change = True
    
    for player in player_ratings.values(): # update player ratings
        if (player.in_game):
            if (player.tid == possession):
                player.team_pts += points_involved
                if poss_change:
                    player.off_poss += 1
            else:
                player.opp_pts += points_involved
                if poss_change:
                    player.def_poss += 1
    
    if poss_change: # change in possession
        for player in player_ratings.values():
            if player.in_game == True:
                if player.tid == possession:
                    player.off_poss += 1
                else:
                    player.def_poss += 1
        for team in teams:
            if team != possession:
                possession = team
                break
    
    prev_gid = curr_gid

def rate(player, on_offense): # method that computes a offensive or defensive rating accordingly for an inputted player
    if on_offense:
        if player.off_poss != 0:
            return 100 * (player.team_pts / player.off_poss)
    else:
        if player.def_poss != 0:
            return 100 * (player.opp_pts / player.def_poss)
    return 0

# arrays to build a dataframe out of
game_ids = []
player_ids = []
off_ratings = []
def_ratings = []
for game, ratings in games_dict.items(): # builds arrays for dataframe by computing and appending player ratings
    for player in ratings:
        game_ids.append(game)
        player_ids.append(player)
        off_rating = rate(games_dict[game][player], True)
        def_rating = rate(games_dict[game][player], False)
        off_ratings.append(off_rating)
        def_ratings.append(def_rating)

# builds dataframe out of arrays; writes dataframe to csv file
d = {'Game_ID' : game_ids, 'Player_ID' : player_ids, 'OffRtg' : off_ratings, 'DefRtg' : def_ratings}
df = pd.DataFrame(d)
df_path = os.path.join('C:/Users/ethan/NBA Hackathon', 'Your_Team_Name_Q1_BBALL.csv')
df.to_csv(df_path)