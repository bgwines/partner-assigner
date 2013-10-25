import copy
import pdb

WALTZ = 0
POLKA = 1

NAMES = 0
PREFS = 1

FOLLOWS = 0
LEADS = 1

debug = False

class Opening_map:
    edges = {}
    leads = []
    follows = []

    def __init__(self):
        pass

    def insert_lead(self, name):
        self.leads.append(name)
        self.edges[name] = ([], ([], []))

    def insert_follow(self, name):
        self.follows.append(name)
        self.edges[name] = ([], ([], []))

    def insert_preference(self, preference):
        self.edges[preference.src][NAMES].append(
            preference.dst
        )
        self.edges[preference.src][PREFS][WALTZ].append(
            preference.weight_waltz
        )
        self.edges[preference.src][PREFS][POLKA].append(
            preference.weight_polka
        )

class DancerState(object):
    name = None
    waltz_partner = None
    polka_partner = None

    def __init__(self, name_param):
        self.name = name_param

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
        self.weight_waltz = int(self.weight_waltz)
        self.weight_polka = int(self.weight_polka)

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
            opening_map.insert_lead(create_dancer(line))
        if curr_state == 'FOLLOWS':
            opening_map.insert_follow(create_dancer(line))
        if curr_state == 'LEAD PREFERENCES':
            opening_map.insert_preference((create_lead_preference(line))            )
        if curr_state == 'FOLLOW PREFERENCES':
            opening_map.insert_preference((create_follow_preference(line))            )

def create_initial_state(leads, follows):
    initial_follow_state = []
    for follow in follows:
        initial_follow_state.append(DancerState(follow))

    initial_lead_state = []
    for lead in leads:
        initial_lead_state.append(DancerState(lead))

    return (initial_follow_state, initial_lead_state)

def gen_next_states(follow_state, lead_state, i):
    curr_lead = lead_state[i].name
    # by direction of DP, curr_lead has both partners free

    next_states = []
    #opt: only enumerate over free ones?
    for w_i, waltz_partner_state in enumerate(follow_state):
        #? (follow_state_copy, lead_state_copy) = (copy.copy(follow_state), copy.copy(lead_state))
        if not waltz_partner_state.free_for_waltz(): continue

        for p_i, polka_partner_state in enumerate(follow_state):
            if not polka_partner_state.free_for_polka(): continue
            if polka_partner_state.name == waltz_partner_state.name: continue

            #opt: fewer copies?
            (follow_state_copy, lead_state_copy) = (copy.deepcopy(follow_state), copy.deepcopy(lead_state))

            #make current assignment
            lead_state_copy[i].set_partners(waltz_partner_state.name, polka_partner_state.name)
            follow_state_copy[w_i].set_waltz_partner(curr_lead)
            follow_state_copy[p_i].set_polka_partner(curr_lead)
            next_states.append(
                (follow_state_copy, lead_state_copy)
            )
    return next_states

def list_of_follow_states_to_count_vector(follow_states):
    l = []
    for follow_state in follow_states:
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

def calc_state_score(state):
    score = 0
    #TODO: dp the score
    for follow_state in state[FOLLOWS]:
        follow_name = follow_state.name
        follow_index = FOLLOW_INDICES[follow_name]

        if not follow_state.free_for_waltz():
            lead_name = follow_state.waltz_partner
            lead_index = LEAD_INDICES[lead_name]

            score += opening_map.edges[follow_name][PREFS][WALTZ][lead_index]
            score += opening_map.edges[lead_name][PREFS][WALTZ][follow_index]
        if not follow_state.free_for_polka():
            lead_name = follow_state.polka_partner
            lead_index = LEAD_INDICES[lead_name]

            score += opening_map.edges[follow_name][PREFS][POLKA][lead_index]
            score += opening_map.edges[lead_name][PREFS][POLKA][follow_index]

    return score

def print_state(state, flag = False):
    matrix = []
    matrix.append([''])
    for lead_state in state[LEADS]:
        matrix[0].append(lead_state.name)

    for i, follow_state in enumerate(state[FOLLOWS]):
        matrix.append([follow_state.name])
        i += 1
        for lead_state in state[LEADS]:
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
    for (follow_state,lead_state) in dp_state:
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
    initial_state = create_initial_state(opening_map.leads, opening_map.follows)
    dp_state = [initial_state]

    for i in xrange(len(opening_map.leads)):
        print '----- DP LEVEL ', i, '-----'
        #curr_leads = opening_map.leads[:(i+1)]
        dp_state = calc_optimal_assignments_with_curr_lead(
            dp_state,
            i
        )
        
        for i, (f_states, l_states) in enumerate(dp_state):
            print i, ': ', list_of_follow_states_to_count_vector(f_states), calc_state_score((f_states, l_states))

        #pdb.set_trace()
        print ''

    return dp_state

def list_to_index_dict(arr):
    d = {}
    for i,e in enumerate(arr):
        d[e] = i
    return d


# globals
opening_map = Opening_map()
fill_map()

THE_LEADS = opening_map.leads
THE_FOLLOWS = opening_map.follows

LEAD_INDICES = list_to_index_dict(THE_LEADS)
FOLLOW_INDICES = list_to_index_dict(THE_FOLLOWS)

# program

final_assignments = dp()

print '- final assignments -'
print print_state(final_assignments[0])
