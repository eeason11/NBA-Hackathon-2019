
# coding: utf-8

# In[135]:


import pandas as pd


# In[486]:


class Player:

    def __init__(self, player_id, game_id, team_id):
        self.player_id = player_id
        self.game_id = game_id
        self.team = team_id
        self.poss_o = 0
        self.poss_d = 0
        self.pts_for = 0
        self.pts_against = 0
        
    def get_team(self):
        return self.team

    def add_points_for(self, pts):
        self.pts_for += pts
        
    def add_points_against(self, pts):
        self.pts_against += pts
    
    def increment_poss_o(self):
        self.poss_o += 1
        
    def increment_poss_d(self):
        self.poss_d += 1
    
    def p_print(self):
        print(self.player_id, self.game_id, self.poss, self.pts_for, self.pts_against)


# In[487]:


class Game:

    def __init__(self):
        self.players = {}

    def add_player(self, player_id, player):
        self.players[player_id] = player
        
    def get_players(self):
        return self.players
    
    def initialize_game(self, game_id, df):
        self.players.clear()
        new_df = df[(df.Game_id == game_id) & (df.Period == 0)]
        for row in new_df.itertuples(): 
            self.players[row.Person_id] = Player(row.Person_id, row.Game_id, row.Team_id)
    


# In[554]:


class Lineup:

    def __init__(self):
        self.lineup = []

    def sub_in(self, player_id):
        self.lineup.append(player_id)
        
    def sub_out(self, player_id):
        self.lineup.remove(player_id)
    
    def initialize_lineup(self, game_id, period, df):
        self.lineup.clear()
        new_df = df[(df.Game_id == game_id) & (df.Period == period)]
        for row in new_df.itertuples(): 
            self.lineup.append(row.Person_id)
    
    def scoring_event(self, pt_value, team_id, game, test):
        for player in self.lineup:
            p = game.players[player]
            game_id = p.game_id
            if p.get_team() == team_id:
                p.add_points_for(pt_value)
            else:
                p.add_points_against(pt_value)
    
    def possesion(self, team_id, game):
        for player in self.lineup:
            p = game.players[player]
            if p.get_team() == team_id:
                p.increment_poss_o()
            else:
                p.increment_poss_d()
        


# In[459]:


lineups = pd.read_csv("Game_Lineup.txt", sep = "\t")
play_by_play = pd.read_csv("Play_by_Play.txt", sep = "\t")
codes = pd.read_csv("Event_Codes.txt", sep = "\t")


# In[462]:


pd.set_option('display.max_rows', 18000)


# In[563]:


#codes


# In[ ]:


play_by_play.sort_values(['Period', 'PC_Time', 'WC_Time', 'Event_Num'], ascending=[True, False, True, True], inplace=True)


# In[471]:


play_by_play = play_by_play.reset_index(drop=True)


# In[552]:


#play_by_play


# In[553]:


#lineups

# In[334]:


def execute_delayed_subs(d_subs):
    while len(d_subs) > 0:
        on_court.sub_out(d_subs.pop())
        on_court.sub_in(d_subs.pop())


# In[558]:


def record_ratings(game, df):
    players = game.get_players()
    for player in players.values():
        g_id = player.game_id
        p_id = player.player_id
        t_id = player.team
        poss_o = player.poss_o
        poss_d = player.poss_d
        points_f = player.pts_for
        points_a = player.pts_against
        if poss_o > 0 or poss_d > 0:
            if poss_o != 0:
                offrtg = (100 * points_f) / poss_o
            if poss_o == 0:
                offrtg = 0
            if poss_d != 0:
                defrtg = (100 * points_a) / poss_d
            if poss_d == 0:
                defrtg = 0
            df = df.append({'Game_ID' : g_id , 'Player_ID' : p_id, 'OffRtg' : offrtg, 'DefRtg' : defrtg} , ignore_index=True)
    return df
    


# In[495]:


P1_team = []
P2_team = []
for i in range(len(play_by_play)):
    row = play_by_play.loc[i] 
    p_id1 = row.Person1
    p_id2 = row.Person2
    new_df1 = lineups[lineups.Person_id == p_id1]
    new_df2 = lineups[lineups.Person_id == p_id2]
    if not new_df1.empty:
        P1_team.append(new_df1.iloc[0].Team_id)
    if new_df1.empty:
        P1_team.append(row.Team_id)
    if not new_df2.empty:
        P2_team.append(new_df2.iloc[0].Team_id)
    if new_df2.empty:
        P2_team.append(row.Team_id)
play_by_play['P1_team'] = P1_team 
play_by_play['P2_team'] = P2_team 


# In[559]:


# Initialize data structures
df = pd.DataFrame(columns=['Game_ID', 'Player_ID', 'OffRtg', 'DefRtg'])
on_court = Lineup()
game = Game()
delayed_subs = []
for i in range(len(play_by_play)):
    row = play_by_play.loc[i] 
    if row.Action_Type == 0 and (row.Event_Msg_Type == 4 or row.Event_Msg_Type == 5):
        continue
    print (i)
    # If beginning of period set lineups
    if row.Event_Msg_Type == 12:
        # if beginning of game set game
        if row.Period == 1:
            game.initialize_game(row.Game_id, lineups)
        on_court.initialize_lineup(row.Game_id, row.Period, lineups)
        continue

    if i + 1 < len(play_by_play) - 1:
        next_row = play_by_play.loc[i+1]
    
    # If made shot, add points and possesion
    if row.Event_Msg_Type == 1:
        on_court.scoring_event(row.Option1, row.P1_team, game, test)
        on_court.possesion(row.P1_team, game)
        continue 
    
    # If ft, make necessary subs and add points / possesions if applicable
    if row.Event_Msg_Type == 3:
        if row.Option1 == 1:
            on_court.scoring_event(row.Option1, row.P1_team, game, test)
            if row.Action_Type in [12, 15]:
                on_court.possesion(row.P1_team, game)
        if row.Action_Type in [10, 12, 15, 19, 20, 26]:
            execute_delayed_subs(delayed_subs)
        
    # If turnover or end of period, add poss
    if row.Event_Msg_Type == 5 or row.Event_Msg_Type == 13:
        on_court.possesion(row.P1_team, game)
        continue
    
    # If miss + reb by other team, add poss
    if row.Event_Msg_Type == 2 and next_row.Event_Msg_Type == 4:
        if row.P1_team != next_row.P1_team:
            on_court.possesion(row.P1_team, game)
            continue 
            
    # If missed ft, add poss
    if row.Event_Msg_Type == 3 and next_row.Event_Msg_Type == 4:
        if row.P1_team != next_row.P1_team:
            on_court.possesion(row.P1_team, game)
            continue 
    
    # If sub, make sub unless it's in between fts then wait until last ft is shot
    if row.Event_Msg_Type == 8:
        j = 1
        while play_by_play.loc[i+j].Event_Msg_Type == 8:
            j += 1
        if play_by_play.loc[i+j].Event_Msg_Type == 3 and play_by_play.loc[i+j].Action_Type in [10, 12, 15, 19, 20, 26]:
            delayed_subs.append(row.Person2)
            delayed_subs.append(row.Person1)
        else:
            on_court.sub_out(row.Person1)
            on_court.sub_in(row.Person2) 
            
    # If game is over record the data
    if row.Event_Msg_Type == 16:
        df = record_ratings(game, df)
       


# In[566]:


#df[df.Game_ID == '006728e4c10e957011e1f24878e6054a'].sort_values(by=['OffRtg'])


# In[583]:


df.sort_values(by='OffRtg')


# In[565]:


#test


# In[582]:


df.to_csv('Caltech_Hoops_Q1_BBALL.csv', sep='\t', index=False)



