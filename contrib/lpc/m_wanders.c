// vi: foldmethod=marker foldlevel=0 syntax=lpc
// $Id: m_wanders.c,v 1.1 2004/08/20 19:46:44 dorn Exp $
//

#define portal

// Variable definitions
int     wanders_freq_rolls          = 6;
int     wanders_freq_sides          = 10;

float   leaves_area                 = 0.0;
float   chance_to_leave_level       = 0.0;
int     current_level_difference    = 0;
int     max_level_difference        = 0;

#ifdef portal
float   chance_to_enter_portal      = 0.0;
#endif

int     wander_at;
int     wander_count;

void force_me(string);

// Function definitions
//  a) M_WANDERS: 
//      1) set_wanders_freq( 2, 8 ); // 2d8 seconds
//      2) set_leaves_level( 1.0 ); // default 0
//      3) set_max_level_difference( 1 ); // How many levels away from home should it wander
//      4) set_leaves_area( 1 ); // (implies leaves_level)

// void renew_wander_at( ) {{{
void renew_wander_at( ) {
    wander_at       = roll(wanders_freq_rolls,wanders_freq_sides);
    wander_count    = 0;
}
// }}}
// void set_wanders_frequency( rolls, die) {{{
void set_wanders_frequency( int rolls, int sides ) {
    if ( (rolls > 0) && (sides > 0) ) {
        wanders_freq_rolls = rolls;
        wanders_freq_sides = sides;
    }
    renew_wander_at();
}
// }}}
// array query_wanders_frequency( ) {{{
array query_wanders_frequency( ) {
    return({ wanders_freq_rolls, wanders_freq_sides });
}
// }}}
// array query_wanders_at( ) {{{
array query_wanders_at( ) {
    return ({ wander_count, wander_at });
}
// }}}
// void set_leaves_level( chance ) {{{
void set_leaves_level( float chance ) {
    if ( chance >= 0 ) {
        chance_to_leave_level = chance;
    } else {
        chance_to_leave_level = 0.0;
    }
}
// }}}
// float query_leaves_level( ) {{{
float query_leaves_level( ) {
    return chance_to_leave_level;
}
// }}}
#ifdef portal
// void set_enters_portal( chance ) {{{
void set_enters_portal( float chance ) {
    if ( chance >= 0 ) {
        chance_to_enter_portal = chance;
    } else {
        chance_to_enter_portal = 0.0;
    }
}
// }}}
// float query_enters_portal( ) {{{
float query_enters_portal( ) {
    return chance_to_enter_portal;
}
// }}}
#endif
// void set_leaves_areay( leave ) {{{
void set_leaves_area( float leave ) {
    if ( leave >= 0.0 ) {
        leaves_area = leave;
    } else {
        leaves_area = 0.0;
    }
}
// }}}
// float query_leaves_area( ) {{{
float query_leaves_area( ) {
    return leaves_area;
}
// }}}
// void set_max_level_difference( difference ) {{{
void set_max_level_difference( int difference ) {
    if ( difference >= 0 ) {
        max_level_difference = difference;
    } else {
        max_level_difference = 0;
    }
}
// }}}
// int query_max_level_difference( ) {{{
int query_max_level_difference( ) {
    return (leaves_area>0.0) ? -1 : max_level_difference;
}
// }}}
// void standard_wander() {{{
void standard_wander() {
    string d;
    array e = ({ });
#ifdef portal
    array p = ({ });
#endif
    object troom;
    object to = this_object();
    object env = environment( to );
    mapping directions = ([ ]);
    int level_vector = 0;
    int full_wander  = ((roll(1,10000)/100.0) <= leaves_area);
    int pid          = 0;   // portal id, so that the mob can "enter <pid> portal"

    if (wander_count++ < wander_at) {
        return;
    } else {
        renew_wander_at();
    }
    if (!env) return;

    foreach( string dir, string fname in env->query_exits()) {
        troom = load_object( fname );

        if ( troom && !troom->is_important_location() ) {
            if ( troom->get_level() > env->get_level() ) {
                level_vector = 1;
            } else if ( troom->get_level() < env->get_level() ) {
                level_vector = -1;
            } else {
                level_vector = 0;
            }

            if ( !full_wander ) {
                if ( troom->get_area() == env->get_area() ) {
                    if ( !level_vector ) {
                        e+=({ dir });
                        directions[dir] = level_vector;
                    } else if ( ( (current_level_difference+level_vector) <=  max_level_difference) && 
                                ( (current_level_difference+level_vector) >= -max_level_difference) ) {
                        // So if the mob is travelling back towards it's home level, let it go
                        // otherwise, check the percentages to see if it really feels like wandering further away from home.
                        if ( (current_level_difference<0) && (level_vector>0) ) {
                            e+=({ dir });
                            directions[dir] = level_vector;
                        } else if ( (current_level_difference>0) && (level_vector<0) ) {
                            e+=({ dir });
                            directions[dir] = level_vector;
                        } else if ( (roll(1,10000)/100.0) <= chance_to_leave_level ) {
                            e+=({ dir });
                            directions[dir] = level_vector;
                        }
                    }
                }
            } else {
                e+=({ dir });
                directions[dir] = level_vector;
            }
        }
    }

#ifdef portal
// portal {{{
    if ( chance_to_enter_portal > 0.0 ) {
        array portals = filter(all_inventory(env), (: $1->get_destination() :) );
        for(int i = 0; i < sizeof(portals); i++) {
            troom = portals[i]->get_destination();
            pid++;

            if ( (roll(1,10000)/100.0) > chance_to_enter_portal ) {
                // Check to see if the mob feels like entering this portal.
                continue;
            }

            if ( troom && !troom->is_important_location() ) {
                if ( troom->get_level() > env->get_level() ) {
                    level_vector = 1;
                } else if ( troom->get_level() < env->get_level() ) {
                    level_vector = -1;
                } else {
                    level_vector = 0;
                }

                if ( !full_wander ) {
                    if ( troom->get_area() == env->get_area() ) {
                        if ( !level_vector ) {
                            p+=({ pid });
                            directions[pid] = level_vector;
                        } else if ( ( (current_level_difference+level_vector) <=  max_level_difference) && 
                                    ( (current_level_difference+level_vector) >= -max_level_difference) ) {
                            // So if the mob is travelling back towards it's home level, let it go
                            // otherwise, check the percentages to see if it really feels like wandering further away from home.
                            if ( (current_level_difference<0) && (level_vector>0) ) {
                                p+=({ pid });
                                directions[pid] = level_vector;
                            } else if ( (current_level_difference>0) && (level_vector<0) ) {
                                p+=({ pid });
                                directions[pid] = level_vector;
                            } else if ( (roll(1,10000)/100.0) <= chance_to_leave_level ) {
                                p+=({ pid });
                                directions[pid] = level_vector;
                            }
                        }
                    }
                } else {
                    p+=({ pid });
                    directions[pid] = level_vector;
                }
            }
        }
    }
// }}}
#endif

    if ( to->following() == to ) {
        if ( sizeof(e) + sizeof(p) ) {
            int     direction = roll(1,sizeof(e)+sizeof(p));
            if (direction<=sizeof(e)) {
                d = choice(e);
                current_level_difference += directions[d];
                force_me("go " + d);
#ifdef portal
            } else {
                string st;
                d = choice(p);
                switch(d) {
                    case 1:     st = "st";  break;
                    case 2:     st = "nd";  break;
                    case 3:     st = "rd";  break;
                    default:    st = "th";  break;
                }
                current_level_difference += directions[d];
                force_me("tell nichus attempting to enter " + d + st + " portal");
                force_me("enter " + d + st + " portal");
#endif
            }
        }
    }
}
// }}}
