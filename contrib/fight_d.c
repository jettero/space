#include <daemons.h>
#include <time.h>

#define ENV(x) environment(x)

//#define DEBUG
//#define ExtraDEBUG

#ifdef DEBUG
#define ROUND    debug("dorn", "-=-=-=-= Round =-=-=-=-\n");
#define SEGMENT  debug("dorn", "-segment "+(i+1)+":\n");
#else
#define ROUND   //
#define SEGMENT //
#endif

#ifdef ExtraDEBUG
#define WHOSMAD  if(aggressions[i][0])\
                    debug("dorn", aggressions[i][0]->query_name() + \
                    " hates " + aggressions[i][1]->query_name() + "!\n")
#define GOTHERE  debug("dorn", "The code got to some \"special\" point!\n")
#define INIT     debug("dorn", "-= Init round =-\n");
#define ADDAGGRE debug("dorn", a->a_short() + " add's aggression at " \
                    + t->a_short()+"\n");
#else
#define WHOSMAD  //
#define GOTHERE  //
#define INIT     //
#define ADDAGGRE //
#endif

private array   aggressions  = ({});
private array   the_round    = ({});
private mapping fighting     = ([]);
private mapping being_fought = ([]);
private mapping special_m    = ([]);

private int round = 0;  // This is either a 0 or a 1, it 
                        // will mark 3/2 and 5/2 turn-ness
                        //
private mapping came_in     = ([]); // This marks weather the player came in
                                    // on a 0 or a 1, so we know if they're
                                    // high or low on their attacks.
                                    // Note that this never gets cleaned out.
                                    // I couldn't think of a good way to do
                                    // it at the time, so I just left it.
                                    // I figure it never gets that big anyway.

mixed is_offensive(object o) { return fighting[o]; }
mixed being_fought(object o) { return being_fought[o]; }
mixed  is_fighting(object o) { return fighting[o]; }

int is_in_range(object a, object t) {
    if(ENV(a) == ENV(t)) {
        if(a->query_altitude() == t->query_altitude() || a->query_weapon()->is_ranged() || t->query_weapon()->is_ranged() ) {
            return 1;
        }
    }

    return 0;
}

void free_hit_on(object t) {
    object a;

    for(int i = sizeof(aggressions)-1; i>=0; i--) {
        if(arrayp(aggressions[i]) && aggressions[i][1] == t) {
            a = aggressions[i][0];

            if(objectp(a) && a->query_awake()) {
                set_this_player(0);
                a->targetted_action("$N $vget a free hit on $t.", t);
                a->query_weapon()->attack(a, t);
            }
        }
    }
}

void perform_nonaggression_pack();

void flee(object t, string dir) {
    if( !objectp(t) )
        return;

    for(int i = sizeof(aggressions)-1; i>=0; i--) {
        if(arrayp(aggressions[i]) && aggressions[i][0] == t)
            aggressions[i] = 0;
    }

    perform_nonaggression_pack();

    t->force_me("say Aiiieeeee!");
    t->go_alone(); /// ditch all followers and degroup
    t->force_me("go " + dir);
}

void add_aggression(object,object);

void do_kill_liv(object a, object t) {
    a->interrupt_study();
    a->interrupt_prayfor();
    a->disturb_spell_casting();

    if(a == t) a->targetted_action("$N tried to kill $t.", t); else {
        fighting[a]     = t;
        being_fought[t] = a;
        map(t->query_group()->query_members(), 
            (: add_aggression($1, $(a)) :)
        );
        aggressions += ({   // Here I'm not overly concerend with   
            ({ a, t })      // weather or not 'a' is already in there. 
        });                 // since the parser already determined that
        came_in[a] = round; // int verb_ob.c
    }
}

void add_aggression(object a, object t) {
    if(!is_offensive(a)) {
        ADDAGGRE

        a->clear_holding(); // there are circumstances where a fight ends without clearing this
                            // starting a new fight with the same person while the holding flags are still set
                            // will cause the fight to start with a hold... 

        do_kill_liv(a, t);
    }                    
}

void calm_down(object a, string msg) {
    for(int i = sizeof(aggressions)-1; i>=0; i--) {
        if(aggressions[i] && aggressions[i][0] == a) {
            if(!aggressions[i][0]->query_unconscious()) {
                aggressions[i][0]->just_calmed_down();
                if(msg) 
                    aggressions[i][0]->simple_action(msg);
            }
            aggressions[i] = 0;
        }
    }
}

int aggression_exists(int index) {
    array t = aggressions[index];
    if( arrayp(t) && objectp(t[0]) && objectp(t[1]) &&
        !( environment(t[0])->is_peace_room() || environment(t[1])->is_peace_room() )
            && is_in_range(t[0], t[1]) && !t[0]->query_ghost() && !t[1]->query_ghost() ) {
        return 1;
    } else {
        aggressions[index] = 0; // This will cause nonaggression pack
    }                          // to delete the aggression if out of range
}                             // et cetera

void perform_nonaggression_pack() {
    mapping tempfg = ([]);
    mapping tempbf = ([]);

    for(int i = sizeof(aggressions)-1; i>=0; i--) {
        if (!aggression_exists(i)) {
            aggressions = aggressions[0..i-1] + aggressions[i+1..];
        } else {
            tempfg[aggressions[i][0]] = aggressions[i][1];
            tempbf[aggressions[i][1]] = aggressions[i][0];
        }
    }

    fighting     = tempfg;
    being_fought = tempbf;
}

int initiative(mixed o) {
    int roll;

    if(objectp(o)) roll = roll(1,10) + ((o) ? o->query_weapon_speed() :0);
    else           roll = roll(1,10) + ((sizeof(o) > 1) ? o[1]        :0);

        roll = (roll>20) ? 20 : roll;
        roll = (roll< 1) ?  1 : roll;
    return (roll-1);
}

void init_round() {
    INIT
    special_m = ([]);
    the_round = ({});
    for(int i = 0; i<20; i++) {
        the_round += ({ ({}) });
    }
}

void add_to_round(int i) {
    object a;

    if(arrayp(aggressions[i])) {
        a = aggressions[i][0];
    }

    WHOSMAD;

    if(a) 
        special_m[a] = a->pop_special_move();

    if(special_m[a]) {
        the_round[ initiative(special_m[a]) ] += ({i});
    } else {
        the_round[ initiative(a)            ] += ({i});
    }
}

void perform_round() {
    int na;
    int aggression_index;
    round = (round+1)%2;

    ROUND

    for(int i = 0; i<sizeof(aggressions); i++) {
        if(arrayp(aggressions[i]))
            if(aggressions[i][0]) 
                aggressions[i][0]->my_action("\n");
    }

    for(int i = 0; i<20; i++) {
        for( int j = 0; j<sizeof(the_round[i]); j++) {
            aggression_index = the_round[i][j];
            if(aggression_exists( aggression_index )) {
                array agg = aggressions[ aggression_index ];
                if(!agg[0]->query_unconscious() && !agg[0]->query_ghost()) {
                    SEGMENT

                    set_this_player(0);

                    if(special_m[agg[0]]) {
                        evaluate(special_m[agg[0]][0]);
                    } else {
                        na = (came_in[agg[0]] == round) ?
                            to_int(agg[0]->query_numoatksf()+0.5) :
                            to_int(agg[0]->query_numoatksf());

                        for (int a = 0; a<na; a++) {
                            if (agg[0] && agg[1]) {
                                if( aggression_exists( aggression_index ) ) {
                                    agg[0]->bodily_functions( "fight" );
                                    agg[0]->query_weapon()->attack(agg[0], agg[1]);
                                } else {
                                    agg[0]->simple_action("$N $vforgo $p next attack.");
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

void fight_loop() {
    remove_call_out("fight_loop");

    if (sizeof(aggressions)) {
        init_round();
        for(int i = 0; i<sizeof(aggressions); i++) {
            add_to_round(i);
        }
        perform_round();
    }
    perform_nonaggression_pack();

    mobs()->less_stunned();
    bodies()->less_stunned();

    call_out( "fight_loop" , rounds(1));

    WATCHER_D->i_am_operating("fight_loop", "the fight daemon", rounds(1));
}

void simulate_error() {
    remove_call_out("fight_loop");

    error("breaking the fight_d intentionally");
}

void create() { fight_loop(); }
