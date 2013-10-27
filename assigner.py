import copy
import pdb

WALTZ = 0
POLKA = 1

NAMES = 0
PREFS = 1

FOLLOWS = 0
LEADS = 1

debug = False

THE_LEAD_OBJS = {}
THE_FOLLOW_OBJS = {}

def insert_lead(name):
    THE_LEAD_OBJS[name] = DancerState(name)

def insert_follow(name):
    THE_FOLLOW_OBJS[name] = DancerState(name)

def insert_preference(preference):
    is_lead = (preference.src in THE_LEAD_OBJS)
    if is_lead:
        THE_LEAD_OBJS[preference.src].set_preference(preference)
    else:
        THE_FOLLOW_OBJS[preference.src].set_preference(preference)

class DancerState(object):

    def __init__(self, name_param):
        self.name = name_param
        self.waltz_partner = None
        self.polka_partner = None
        self.heart = (None, None) #person, dance
        self.waltz_prefs = {}
        self.polka_prefs = {}

    def set_preference(self, preference):
        self.waltz_prefs[preference.dst] = preference.weight_waltz
        self.polka_prefs[preference.dst] = preference.weight_polka

        if preference.weight_waltz == '<3':
            self.heart = (preference.dst, WALTZ)
        if preference.weight_polka == '<3':
            self.heart = (preference.dst, POLKA)

    def has_heart(self):
        return self.heart != (None, None)

    def get_heart(self):
        return self.heart

    def set_heart(self, heart_param):
        self.heart = heart_param

    def set_waltz_partner(self, waltz_partner_param):
        self.waltz_partner = waltz_partner_param

    def set_polka_partner(self, polka_partner_param):
        self.polka_partner = polka_partner_param

    def set_partners(self, waltz_partner_param, polka_partner_param):
        self.waltz_partner = waltz_partner_param
        self.polka_partner = polka_partner_param

    def fully_assigned(self):
        return (self.waltz_partner != None
            and self.polka_partner != None)

    def free_for_polka(self):
        return self.polka_partner == None

    def free_for_waltz(self):
        return self.waltz_partner == None

    def count_dances_taken(self):
        n = 2
        if self.free_for_waltz(): n -= 1
        if self.free_for_polka(): n -= 1
        return n

    def __repr__(self):
        return self.name + ' : (w,p)=(' + str(self.waltz_partner) + ',' + str(self.polka_partner) + ')' 

class Preference(object):
    src = None
    dst = None
    weight_waltz = None
    weight_polka = None

    def __init__(self, gender, line):
        (self.src, self.weight_waltz, self.weight_polka, self.dst) = line.split(' ')

    def __repr__(self):
        return self.src + ' -> ' + self.dst + ': (w,p)=(' + str(self.weight_waltz) + ',' + str(self.weight_polka) + ')' 

#Parser methods
def create_dancer(line):
    return line

def create_lead_preference(line):
    return Preference('LEAD', line)

def create_follow_preference(line):
    return Preference('FOLLOW', line)

STATES = ['LEADS', 'FOLLOWS', 'LEAD PREFERENCES', 'FOLLOW PREFERENCES']

def fill_map(filename = 'opening.txt'):
    file = open(filename, "r")
    line = ''
    curr_state = None
    for line in file:
        line = line.strip()
        if line in STATES:
            curr_state = line
            continue
        if line == '' or line[0] == '#':
            continue

        if curr_state == 'LEADS':
            insert_lead(create_dancer(line))
        elif curr_state == 'FOLLOWS':
            insert_follow(create_dancer(line))
        elif curr_state == 'LEAD PREFERENCES':
            insert_preference((create_lead_preference(line)))
        elif curr_state == 'FOLLOW PREFERENCES':
            insert_preference((create_follow_preference(line)))

def create_initial_state():
    return (THE_FOLLOW_OBJS, THE_LEAD_OBJS)

def list_of_follow_states_to_count_vector(follow_states):
    l = []
    for (follow_name, follow_state) in follow_states.items():
        l.append(follow_state.count_dances_taken())
    return tuple(l)

def make_state_buckets(states):
    state_buckets = {}
    for state in states:
        state_count_vector = list_of_follow_states_to_count_vector(state[FOLLOWS])
        if state_count_vector in state_buckets:
            state_buckets[state_count_vector].append(state)
        else:
            state_buckets[state_count_vector] = [state]
    return state_buckets

X = -1
HEART = 100#TODO
BAD_STATE = 18 * 2 * (-100)
def calc_value(ranking):
    if ranking == 'X':
        return X
    elif ranking == '<3':
        return HEART
    else:
        return int(ranking)

def calc_state_score(state):
    score = 0
    #TODO: dp the score
    for (follow_name, follow_state) in state[FOLLOWS].items():
        if not follow_state.free_for_waltz():
            lead_name = follow_state.waltz_partner

            value_a = calc_value(follow_state.waltz_prefs[lead_name])
            value_b = calc_value(THE_LEAD_OBJS[lead_name].waltz_prefs[follow_name])
            if value_a == X or value_b == X:
                return BAD_STATE
            score += value_a + value_b

        if not follow_state.free_for_polka():
            lead_name = follow_state.polka_partner

            value_a = calc_value(THE_FOLLOW_OBJS[follow_name].polka_prefs[lead_name])
            value_b = calc_value(THE_LEAD_OBJS[lead_name].polka_prefs[follow_name])
            if value_a == X or value_b == X:
                return BAD_STATE
            score += value_a + value_b

    return score

def print_state(state, flag = False):
    matrix = []
    matrix.append([''])
    for (lead_name, lead_state) in state[LEADS].items():
        matrix[0].append(lead_state.name)

    i=0;
    for (follow_name, follow_state) in state[FOLLOWS].items():
        matrix.append([follow_state.name])
        i += 1
        for (lead_name, lead_state) in state[LEADS].items():
            if follow_state.waltz_partner == lead_state.name:
                matrix[i].append('W')
            elif follow_state.polka_partner == lead_state.name:
                matrix[i].append('P')
            else:
                matrix[i].append('-')

    for line in matrix:
        print '\t\t',
        if flag:
            print '\t',
        print line
    #for i, follow_state in enumerate(state[FOLLOWS]):


def calc_opt_state(states):
    if debug: print '-- new bucket of size ', len(states), ' --'

    best_state = None
    best_state_score = None
    for state in states:
        state_score = calc_state_score(state)

        if debug: print '\tstate score ', state_score, ' for state: ', state
        if debug: print_state(state)

        if state_score > best_state_score:
            best_state_score = state_score
            best_state = state

    if debug: print '\topt state:'
    if debug: print_state(best_state, True)

    return best_state

def gen_next_states(follow_state, lead_state, curr_lead):
    # by direction of DP, curr_lead has both partners free

    next_states = []
    #opt: only enumerate over free ones?
    for (waltz_partner_name, waltz_partner_state) in follow_state.items():
        #? (follow_state_copy, lead_state_copy) = (copy.copy(follow_state), copy.copy(lead_state))
        if not waltz_partner_state.free_for_waltz(): continue

        for (polka_partner_name, polka_partner_state) in follow_state.items():
            if not polka_partner_state.free_for_polka(): continue
            if polka_partner_state.name == waltz_partner_state.name: continue

            (follow_state_copy, lead_state_copy) = (copy.deepcopy(follow_state), copy.deepcopy(lead_state))

            #make current assignment
            lead_state_copy[curr_lead].set_partners(waltz_partner_state.name, polka_partner_state.name)
            follow_state_copy[waltz_partner_name].set_waltz_partner(curr_lead)
            follow_state_copy[polka_partner_name].set_polka_partner(curr_lead)
            next_states.append(
                (follow_state_copy, lead_state_copy)
            )
    return next_states

def collapse_states(states):
    if len(states) == 1:
        #optimization
        return states

    state_buckets = make_state_buckets(states)

    collapsed_states = []
    for (count_vector, bucketed_states) in state_buckets.items():
        opt_state = calc_opt_state(bucketed_states)
        collapsed_states.append(opt_state)
    return collapsed_states

def calc_optimal_assignments_with_curr_lead(dp_state, i):
    new_dp_state = []

    new_states = []
    for (follow_state, lead_state) in dp_state:
        states_from_curr_state = gen_next_states(follow_state, lead_state, i)
        for state_from_curr_state in states_from_curr_state:
            new_states.append(state_from_curr_state)

    collapsed_states = collapse_states(new_states)
    for collapsed_state in collapsed_states:
        new_dp_state.append(collapsed_state)

    return new_dp_state

def dp():
    """
    dp_state = [[DancerState], [DancerState], [DancerState], ...]
        where [DancerState] = a list of assignments, one of <=3^18
    """
    initial_state = create_initial_state()
    dp_state = [initial_state]

    for j,lead in enumerate(THE_LEAD_OBJS):
        print '----- DP LEVEL ', j, '-----'
        dp_state = calc_optimal_assignments_with_curr_lead(
            dp_state,
            lead
        )
        
        for i, (f_states, l_states) in enumerate(dp_state):
            print i, ': ', list_of_follow_states_to_count_vector(f_states), calc_state_score((f_states, l_states))

        print ''

    return dp_state

def list_to_index_dict(arr):
    d = {}
    for i,e in enumerate(arr):
        d[e] = i
    return d


# globals
fill_map()

# program

final_assignments = dp()

print '- final assignments -'
print print_state(final_assignments[0])
