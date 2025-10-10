#include <mudlib.h>
#include <moon_names.h>
#include <light.h>
#include <time.h>

inherit M_DAEMON_DATA;

int cTime;

int get_cTime() {
    return cTime;
}

int get_tod() {
    int ti = cTime%24;

    return (ti) ? ti : 24;
}

int get_dom() {
    return ( (cTime/22) %36 ) +1;
}

int get_doy()  { return (cTime/24)%365 +1; }
int get_year() { return (cTime/8760);      }

int query_daytime() {
    switch(get_tod()) {
        case 6..20: return 1;
        case 21..5: return 0;
    }
}

int query_nighttime() {
    return !query_daytime();
}

int get_moon_phase() {
    int dom = get_dom();

    switch(dom) {
        case  1..9 : return NEW   ;
        case 10..18: return WAXING;
        case 19..27: return FULL  ;
        case 28..36: return WANING;
    }

    error("bad moon date...");
    return -1;
}

int casting_level_bonus(object o) {
    /*
    if( objectp(o) && o->is_aligned() ) {
        int my_moon = o->is_good() ? WHITE_MOON : o->is_evil() ? BLACK_MOON : RED_MOON;
        case( my_moon ) {
            default:
                
        }
    }
    */

    return 0;
}

int query_light() {
    if ( query_daytime() )
        return VERY_MUCH_LIGHT;

    if ( get_moon_phase() == FULL )
        return MUCH_LIGHT; 

    if ( get_moon_phase() == WAXING || get_moon_phase() == WANING )
        return LITTLE_LIGHT;

    return 0;
}

string announce_moon_phase_change(int phase) {
    switch(phase) {
        case    NEW:  return "The Moon has just entered low sanction.  ";
        case   FULL:  return "The Moon has just entered high sanction.  ";
        case WAXING:  return "The Moon just began the waxing phase.  ";
        case WANING:  return "The Moon just began the waning phase.  ";
    }
}

void time_loop() {
    string time_message = "";

    int pmp = 0;
    int cmp = 0;

    int are_full, are_new;
    int were_full, were_new;

    remove_call_out("time_loop");

    pmp = get_moon_phase();

    if(pmp == NEW)
        were_new++;

    if(pmp == FULL)
        were_full++;

    cTime++;

    cmp = get_moon_phase();

    if(get_tod() ==  6) time_message += "The sun rises.  ";
    if(get_tod() == 21) time_message += "The sun sets.  ";

    if ( cmp != pmp ) {
        time_message += announce_moon_phase_change(cmp);

        if( cmp == NEW )
            INN_D->rent_is_due();
    }

    if(cmp == FULL)
        are_full++;

    if(cmp == NEW)
        are_new++;

    foreach(object o in bodies()) {
        if( time_message != "") 
            o->my_action(time_message);

        o->bodily_functions( "time" );  // includes hair and beard
    }


    WATCHER_D->i_am_operating("time_loop", "the time daemon", HOUR_LENGTH);
    call_out( "time_loop", HOUR_LENGTH);

    save_me();
}

void do_a_day() {
    for(int i=0; i<24; i++) {
        time_loop();
    }
}

void create() {
    ::create();

    call_out( "time_loop", 0);
}

string stat_me() {
    return sprintf("    Time = %d
    Time %d O'clock
    Day of month: %d of 36
    Date: %d of the year %d\n", 
       cTime,
       get_tod(), get_dom(),
       get_doy(),
       get_year() );
}

string time_str() {
    return sprintf("    Time %d O'clock
    Day of month: %d of 36
    Date: %d of the year %d\n", 
       get_tod(), get_dom(),
       get_doy(),
       get_year() );
}

void simulate_error() {
    remove_call_out("time_loop");

    error("breaking the time_d intentionally");
}
