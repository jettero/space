#include <daemons.h>

inherit MONSTER;
inherit M_ACTIONS;
inherit M_TRIGGERS;
inherit M_SMARTMOVE;

void random_behaviors();
void do_game_command(string);
array query_adj();
array query_id();

string a_short();
string short();
int query_unique();

int array activity = ({2,6});
int exp_award;

int is_a_mob = 0;

int unique_id;

void set_uid(int i) { unique_id = i; }
int  query_uid()    { return unique_id; }

string query_title() {
    return this_object()->short();
}

string in_room_desc() {
    string result;
    result = capitalize(a_short());

    result += this_object()->query_condition_str();

    return result;
}

string query_name() {
    string ret = a_short();

    if(query_unique())
        ret = the_short();

    return ret;
}

void do_receive(string s) {
    m_triggers::do_receive(s);
}

void receive_inside_msg( string str) { do_receive(str); }
void receive_outside_msg(string str) { do_receive(str); }
void receive_private_msg(string str) { do_receive(str); }

int    is_just_a_mob() { return is_a_mob; }
int    is_mob()        { return is_a_mob; }
object query_body()    { return (is_a_mob) ? this_object() : 0; }

void set_exp_award(int x) {
    exp_award = x;
}

int query_exp_award() {
    if(exp_award)
        return exp_award;

    return ::query_exp_award();
}

void set_activity_frequency(int n, int s) {
    activity = ({n,s});
}

void mudlib_setup() {
    set_def_msgs("living-default");
    call_out( "random_behaviors", roll(activity[0], activity[1]) );
    MOB_D->I_exist();
    is_a_mob=1;
}

void try_to_kill_someone() {
    object to  = this_object();
    object env = (to)  ? environment( to )  : 0;
    array  aie = (env) ? all_inventory(env) : 0;

    if(sizeof(aie)) {
        aie = filter(aie, (: $1->is_living() && $1->query_id() :) );
        aie -= ({ to });
    }

    if(sizeof(aie)) {
        do_game_command("kill " + aie[random(sizeof(aie))]->query_id()[0]);
    }
}
    
void random_behaviors() {
    this_object()->have_behavior();
    call_out( "random_behaviors", roll(activity[0], activity[1]) );
}
