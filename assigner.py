import copy
import pdb
import sys
import thread

WALTZ = 0
POLKA = 1

NAMES = 0
PREFS = 1

FOLLOWS = 0
LEADS = 1

NAME = 0
FIRST_YEAR_STATUS = 1
IS_FIRST_YEAR = '1'

SCORE_METRIC = None
SCORE_METRIC_MAX_MIN_ASSIGNMENT = 0
SCORE_METRIC_MAX_SUM = 1

debug_flag = False
status_flag = True

THE_LEAD_OBJS = {}
THE_FOLLOW_OBJS = {}

STATES = set(['LEADS', 'FOLLOWS', 'LEAD PREFERENCES', 'FOLLOW PREFERENCES'])

def insert_lead(dancer):
    if len(dancer) == 1:
        dancer.append('NOT_FIRST_YEAR')

    THE_LEAD_OBJS[dancer[NAME]] = DancerState(dancer[NAME], dancer[FIRST_YEAR_STATUS])

def insert_follow(dancer):
    if len(dancer) == 1:
        dancer.append('NOT_FIRST_YEAR')
    
    THE_FOLLOW_OBJS[dancer[NAME]] = DancerState(dancer[NAME], dancer[FIRST_YEAR_STATUS])

def insert_preference(preference):
    is_lead = (preference.src in THE_LEAD_OBJS)
    if is_lead:
        THE_LEAD_OBJS[preference.src].set_preference(preference)
    else:
        THE_FOLLOW_OBJS[preference.src].set_preference(preference)

class DancerState:
    def __init__(self, dancer_name, first_year_status):
        self.name = dancer_name
        self.waltz_partner = None
        self.polka_partner = None
        self.heart = (None, None) #person, dance
        self.waltz_prefs = {}
        self.polka_prefs = {}
        self.can_be_alternate = (first_year_status == IS_FIRST_YEAR)

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

class Preference:
    src = None
    dst = None
    weight_waltz = None
    weight_polka = None

    def __init__(self, gender, line):
        (self.src, self.weight_waltz, self.weight_polka, self.dst) = line.split(' ')

    def __repr__(self):
        return self.src + ' -> ' + self.dst + ': (w,p)=(' + str(self.weight_waltz) + ',' + str(self.weight_polka) + ')' 

class AssignmentState:
    def __init__(self, follow_state = [], lead_state = []):
        self.follow_state = follow_state
        self.lead_state = lead_state
        self.waltz_alternates = []
        self.polka_alternates = []

#Parser methods
def create_dancer(line):
    return line.split()

def create_lead_preference(line):
    return Preference('LEAD', line)

def create_follow_preference(line):
    return Preference('FOLLOW', line)

def insert_alternate_objs():
    insert_lead(create_dancer('ALTERNATE1L 1'))
    insert_lead(create_dancer('ALTERNATE2L 1'))
    insert_follow(create_dancer('ALTERNATE1F 1'))
    insert_follow(create_dancer('ALTERNATE2F 1'))

    for lead_name in THE_LEAD_OBJS.keys():
        # 0: TODO (max / min if 1-18)
        insert_preference(create_follow_preference('ALTERNATE1F 1 1 ' + lead_name))
        insert_preference(create_follow_preference('ALTERNATE2F 1 1 ' + lead_name))

    for follow_name in THE_FOLLOW_OBJS.keys():
        # 0: TODO (max / min if 1-18)
        insert_preference(create_lead_preference('ALTERNATE1L 1 1 ' + follow_name))
        insert_preference(create_lead_preference('ALTERNATE2L 1 1 ' + follow_name))


def read_in_data(filename = 'opening.txt'):
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

    insert_alternate_objs()

def create_initial_state():
    return (THE_FOLLOW_OBJS, THE_LEAD_OBJS)

def list_of_follow_states_to_count_vector(follow_states):
    l = []
    for (follow_name, follow_state) in follow_states.items():
        l.append(follow_state.count_dances_taken())
    return tuple(l)

#
def make_state_buckets_old(states):
    state_buckets = {}
    for state in states:
        state_count_vector = list_of_follow_states_to_count_vector(state[FOLLOWS])
        if state_count_vector in state_buckets:
            state_buckets[state_count_vector].append(state)
        else:
            state_buckets[state_count_vector] = [state]
    return state_buckets

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

def get_scores_from_state(state):
    scores = []
    #TODO: dp the score
    for (follow_name, follow_state) in state[FOLLOWS].items():
        if not follow_state.free_for_waltz():
            lead_name = follow_state.waltz_partner

            value_a = calc_value(follow_state.waltz_prefs[lead_name])
            value_b = calc_value(THE_LEAD_OBJS[lead_name].waltz_prefs[follow_name])
            scores.append(value_a)
            scores.append(value_b)

        if not follow_state.free_for_polka():
            lead_name = follow_state.polka_partner

            value_a = calc_value(THE_FOLLOW_OBJS[follow_name].polka_prefs[lead_name])
            value_b = calc_value(THE_LEAD_OBJS[lead_name].polka_prefs[follow_name])
            scores.append(value_a)
            scores.append(value_b)

    return scores

SENTINEL = -2
def calc_state_score_max_min_assignment(scores):
    min_score = SENTINEL
    for score in scores:
        if min_score == SENTINEL or score < min_score:
            min_score = score
    return min_score

def calc_state_score_max_sum(scores):
    sum = 0
    for score in scores:
        sum += score
    return sum

def calc_state_score(state):
    scores = get_scores_from_state(state)

    if SCORE_METRIC == SCORE_METRIC_MAX_MIN_ASSIGNMENT:
        return calc_state_score_max_min_assignment(scores)
    elif SCORE_METRIC == SCORE_METRIC_MAX_SUM:
        return calc_state_score_max_sum(scores)
    else:
        return -1

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
    scores_for_printing = []
    state_vector_for_printing = list_of_follow_states_to_count_vector(states[0][FOLLOWS])

    best_state = None
    best_state_score = None
    for state in states:
        state_score = calc_state_score(state)
        scores_for_printing.append(state_score)

        if debug_flag: print '\tstate score ', state_score, ' for state: ', state
        if debug_flag: print_state(state)

        if state_score > best_state_score:
            best_state_score = state_score
            best_state = state

    if status_flag:
        print '\t--', state_vector_for_printing, ': state vector bucket size: ', len(states),
        print 'scores (opt:', best_state_score, '): ', scores_for_printing

    return best_state

def both_are_alternates(lead_name, follow_name):
    if (len(lead_name) != len('ALTERNATE**') or
        len(follow_name) != len('ALTERNATE**')):
        return False

    return (lead_name[0:len('ALTERNATE')] == 'ALTERNATE' and 
            follow_name[0:len('ALTERNATE')] == 'ALTERNATE')

def gen_next_states(follow_state, lead_state, curr_lead):
    # by direction of DP, curr_lead has both partners free

    next_states = []
    #opt: only enumerate over free ones?
    for (waltz_partner_name, waltz_partner_state) in follow_state.items():
        #? (follow_state_copy, lead_state_copy) = (copy.copy(follow_state), copy.copy(lead_state))
        if (not waltz_partner_state.free_for_waltz()
            or both_are_alternates(curr_lead, waltz_partner_name)):
            continue

        for (polka_partner_name, polka_partner_state) in follow_state.items():
            if (not polka_partner_state.free_for_polka()
                or polka_partner_state.name == waltz_partner_state.name
                or both_are_alternates(curr_lead, polka_partner_name)
                or both_are_alternates(waltz_partner_name, polka_partner_name)):
                continue

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
    print 'calculating...'
    initial_state = create_initial_state()
    dp_state = [initial_state]

    for j,lead in enumerate(THE_LEAD_OBJS):
        if status_flag:
            print '----- adding lead #', j, '-----'
        dp_state = calc_optimal_assignments_with_curr_lead(
            dp_state,
            lead
        )

    return dp_state

def selection_not_valid(selection):
    return (selection != SCORE_METRIC_MAX_MIN_ASSIGNMENT
        and selection != SCORE_METRIC_MAX_SUM)

def determine_score_metric():
    selection = SCORE_METRIC_MAX_SUM
    while selection_not_valid(selection):
        print 'Select a score metric:'
        print '\t(', 0, ') max-min'
        print '\t(', 1, ') max-sum'
        selection = input()

    global SCORE_METRIC
    SCORE_METRIC = selection

def print_assignments(assignments):
    print '\n- final assignments -'
    print print_state(assignments)

FILENAME = 1
def __main__():
    determine_score_metric()
    read_in_data(sys.argv[FILENAME])

    final_assignments = dp()
    print_assignments(final_assignments[0])

if __name__ == '__main__':
    __main__()