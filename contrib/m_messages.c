// vi:fdm=marker fdl=0:
// This is from an ancient version of the lima-mudos mudlib. I had to go
// digging through some tape archives from circa y2k to find this ymmv.  I'm
// not sure what kind of attribution I could ever put here to link back to
// where I found it. It probably had a copyright notice at the top at one point
// -- and I almost certainly wasn't supposed to remove it, but in any case, I
// don't have it.
//
// Let me know if this is a problem for you and I'll fix it or remove it.

#include <mudlib.h>

//:MODULE
// The message module.  The correct way to compose and send any messages
// To users is using this module, as it will automatically get the grammar
// right for each person involved.

/* More simul conversion fall out */
string punctuate(string);
static private string vowels = "aeiouAEIOU";

#define A_SHORT(x)   (objectp(x) ? x->a_short() : (member_array(x[0], vowels) == -1 ? "a " : "an ") + x)
#define SHORT(x)     (objectp(x) ? x->short() : x)
#define THE_SHORT(x) (objectp(x) ? x->the_short() : "the " + x)
mapping messages = ([]);
mapping def_messages = ([]);

void set_def_msgs(string type) {
    if (type == "living-default")
    if (!(def_messages = ([ "leave": "$N $vleave $o.",
                            "mleave": "$N $vdisappear in a puff of smoke.",
                            "enter": "$N $venter $o.",
                            "menter": "$N $vappear in a puff of smoke.",
                            "invis": "$N $vfade from view.",
                            "vis": "$N $vfade into view.",
                            "home": "$N $vgo home.",
                            "clone": "$N $vcreate $o.",
                            "destruct": "$N $vdestruct $o.",
                          ])));
}

// void add_msg(string cls, string msg) {{{
void add_msg(string cls, string msg) {
    if (!messages) messages = ([]);
    if (pointerp(messages[cls]))
	messages[cls] += ({ msg });
    else if (messages[cls]) {
	messages[cls]=({ messages[cls], msg });
    } else
	messages[cls]=msg;
}
// }}}
// string query_msg(string which) {{{
string query_msg(string which) { 
    return messages[which] || def_messages[which]; 
}
// }}}
// void set_msgs(string cls, string *msgs) {{{
void set_msgs(string cls, string *msgs) {
    if (!messages) messages = ([]);
    if(!msgs || !sizeof(msgs))  {
	map_delete(messages, cls);
	return;
    }
    messages[cls] = msgs;
}
// }}}
// void clear_messages() {{{
void clear_messages() {
    messages = ([]);
}
// }}}
// stjing *query_msg_types() {{{
string *query_msg_types() {
    return clean_array(keys(messages) + keys(def_messages));
}
// }}}
// varargs string compose_message(object forwhom, string msg, object *who, array obs...) {{{
//:FUNCTION compose_message
//The lowest level message composing function; it is passed the object
//for whom the message is wanted, the message string, the array of people
//involved, and the objects involved.  It returns the appropriate message.
//Usually this routine is used through the higher level interfaces.
varargs string compose_message(object forwhom, string msg, object *who, array obs...) {
    mixed ob;
    mixed *fmt;
    string res;
    int i,j,c;
    int num, subj;
    string str;
    string bit;
    mapping has = ([]);
    int loop;
    int skipme;

    // $T {{,}} to gender {{{
    if( sizeof(who)>1 && objectp(who[1]) ) {
        fmt = reg_assoc(msg, ({ "\\[\\[", "\\++", "\\]\\]" }), ({ 1, 2, 3 }) );
        c = sizeof(fmt[1]) - 1;
        foreach(int p in fmt[1]) {
            if( p+4 <= c ) {
                if( fmt[1][p] == 1 && fmt[1][p+2] == 2 && fmt[1][p+4] == 3 ) {
                    c = who[1]->query_gender();
                    msg = "";
                    for(j=0; j<sizeof(fmt[0]); j++)
                        if( !fmt[1][j] ) {
                            if( skipme )
                                skipme = 0;
                            else
                                msg += fmt[0][j];
                        } else if( (fmt[1][j] == 1 && c == 2) || (fmt[1][j] == 2 && c == 1) ) {
                                skipme = 1;
                        }
                }
            }
        }
    }
    // }}}
    // $N {,} to gender {{{
    if( sizeof(who)>0 && objectp(who[0]) ) {
        fmt = reg_assoc(msg, ({ "{{", ",,", "}}" }), ({ 1, 2, 3 }) );
        c = sizeof(fmt[1]) - 1;
        foreach(int p in fmt[1]) {
            if( p+4 <= c ) {
                if( fmt[1][p] == 1 && fmt[1][p+2] == 2 && fmt[1][p+4] == 3 ) {
                    c = who[0]->query_gender();
                    msg = "";
                    for(j=0; j<sizeof(fmt[0]); j++)
                        if( !fmt[1][j] ) {
                            if( skipme )
                                skipme = 0;
                            else
                                msg += fmt[0][j];
                        } else if( (fmt[1][j] == 1 && c == 2) || (fmt[1][j] == 2 && c == 1) ) {
                                skipme = 1;
                        }
                }
            }
        }
    }
    // }}}

    fmt = reg_assoc(msg, ({ "\\$[MmNnVvTtPpOoRrWw][a-z0-9]*" }), ({ 1 }) );
    fmt = fmt[0]; // ignore the token info for now
    
    res = fmt[0];
    i=1;
    while (i<sizeof(fmt)) {
	c = fmt[i][1];

	if (fmt[i][2] && fmt[i][2]<'a') {
	    if (fmt[i][3] && fmt[i][3] < 'a') {
		subj = fmt[i][2] - '0';
		num = fmt[i][3] - '0';
		str = fmt[i][4..<0];
	    } else {
		subj = 0;
		num = fmt[i][2] - '0';
		str = fmt[i][3..<0];
	    }
	} else {
	    subj = 0;
	    num = ((c == 't' || c == 'T') ? 1 : 0); // target defaults to 1, not zero
	    str = fmt[i][2..<0];
	}

    // debug("dorn", num, subj, c);

        loop = 1;
        while(loop) {
            loop = 0;  // used to get the case 'w' to work right ...
            switch (c) {
                case 'm':
                case 'M':
                    bit = who[num]->query_name();
                    break;
                    // otherwize, fall through
                case 'w':
                case 'W':
                    bit = who[num]->query_worship();
                    bit = (sizeof(bit)) ? bit : "The AEsir";
                    if(who[num]->short() == bit) {
                        if(str == "p") {
                            c    = 'p';
                            str  = "";
                            bit  = "";
                            loop = 1;
                        } else {
                            if(str == "n") {
                                c    = 'n';
                                str  = "";
                                bit  = "";
                                loop = 1;
                            } else {
                                c    = 'r';
                                str  = "";
                                bit  = "";
                                loop = 1;
                            }
                        }
                    } else {
                        if(str == "p") {
                            if(bit[<1] != 's') {
                                bit += "'s";
                            } else {
                                bit += "'";
                            }
                        }
                    }
                    break;
                    // otherwize, fall through
                case 'o':
                case 'O':
                    ob = obs[num];
                    if (objectp(ob) && has[ob]) {
                        bit = ob->query_pronoun();
                        bit = stringp(bit) ? bit : "it";
                    } else {
                        if(objectp(ob)) {
                            switch(str) {
                                case "t": bit = THE_SHORT(ob); break;
                                case "s": bit =     SHORT(ob); break;
                                default:
                                    bit = A_SHORT(ob);
                            }
                        } else {
                            bit = ob;
                        }

                        has[ob]++;
                    }
                    break;
                case 't':
                case 'T':
                    if (str=="") {
                        str = "o";
                    }
                    if (who[num] == who[subj]) {
                        str = "r";
                    }
                    /* Only difference between $n and $t is that $t defaults to $n1o */
                    /* and $t goes to $n1r if the $n matches the this_object() */
                    /* Fall through */
                case 'n':
                case 'N':
                    if (str=="") 
                        str = "s";
                    if (str != "p") {
                        if (subj < sizeof(who) && (who[subj] == who[num]) && has[who[subj]]) {
                            if (str == "o") {
                                if (forwhom == who[subj]) {
                                    bit = "you";
                                } else {
                                    bit = who[subj]->query_objective();
                                }
                            }
                            else if (str == "r") {
                                if (forwhom == who[subj]) {
                                    bit = "yourself";
                                } else {
                                    bit = who[subj]->query_reflexive();
                                }
                            }
                            else if (str == "s") {
                                if (forwhom == who[subj]) {
                                    bit = "you";
                                } else {
                                    bit = who[subj]->query_subjective();
                                }
                            }
                            break;
                        }
                        /* Other pronouns */
                        if (who[num]==forwhom) {
                            bit = "you";
                            has[who[num]]++;
                            break;
                        }
                        if (has[who[num]]) {
                            if (str[0]=='o') bit = who[num]->query_objective();
                            else bit = who[num]->query_subjective();
                            break;
                        }
                    }
                    has[who[num]]++;
                    /*bit = (objectp(who[num]) && who[num]->is_just_a_mob()) ?
                          who[num]->a_short() : who[num]->short();*/
                    bit = (objectp(who[num])) ? str=="a" ? 
                        who[num]->is_just_a_mob() ? who[num]->a_short() : who[num]->a_nondead_short() 
                        : who[num]->a_short() : bit;
                  //bit = (objectp(who[num]) && !who[num]->is_visible()) ?  "someone" : bit;
                    break;
                case 'R':
                case 'r':
                    if (forwhom == who[num]) {
                        bit = "yourself";
                    } else {
                        bit = who[num]->query_reflexive();
                    }
                    break;
                case 'v':
                case 'V':
                    /* hack for contractions */
                    if (i + 1 < sizeof(fmt) && fmt[i+1][0..2] == "'t ") {
                        str += "'t";
                        fmt[i+1] = fmt[i+1][2..];
                    }
                    
                    if (num >= sizeof(who) || who[num]!=forwhom) bit = M_GRAMMAR->pluralize(str);
                    else bit = str;
                    break;
                case 'p':
                case 'P':
                    if (forwhom == who[num]) {
                        bit = "your";
                        break;
                    }
                    if (has[who[num]]) {
                        bit = who[num]->query_possessive();
                        break;
                    }
                    bit = who[num]->query_named_possessive();
                    has[who[num]]++;
                    break;
            } // end switch
        }   // end while
	  // hack to prevent errors.
	if (!bit) bit = "";
	if (c < 'a') bit = capitalize(bit);
	if (fmt[i+1][0] == '.')
	    res += M_GRAMMAR->punctuate(bit) + fmt[i+1][1..];
	else
	    res += bit + fmt[i+1];
	i+=2;
    }
    if( res[<1] != '\n' ) 
	res += "\n";
    return res;
}
// }}}
// varargs string *action(object *who, mixed msg, array obs...) {{{
//:FUNCTION action
//Make the messages for a given group of people involved.  The return
//value will have one array per person, as well as one for anyone else.
//inform() can be used to send these messages to the right people.
//see: inform
varargs string *action(object *who, mixed msg, array obs...) {
    int i;
    string *res;

    if (pointerp(msg))
	msg = msg[random(sizeof(msg))];
    res = allocate(sizeof(who)+1);
    for (i=0; i<sizeof(who); i++) {
	res[i] = compose_message(who[i], msg, who, obs...);
    }
    res[sizeof(who)]=compose_message(0, msg, who, obs...);
    return res;
}
// }}}
// void inform(object *who, string *msgs, mixed others) {{{
//:FUNCTION inform
//Given an array of participants, and an array of messages, and either an
//object or array of objects, deliver each message to the appropriate
//participant, being careful not to deliver a message twice.
//The last arg is either a room, in which that room is told the 'other'
//message, or an array of people to recieve the 'other' message.
void inform(object *who, string *msgs, mixed others) {
    int i;
    mapping done = ([]);
    for (i=0; i<sizeof(who); i++) {
	if (done[who[i]]) continue;
	done[who[i]]++;
	tell(who[i], msgs[i], MSG_INDENT);
    }
    if (pointerp(others)) {
	map_array(others - who, (: tell($1, $(msgs[<1]), MSG_INDENT) :));
    }
    else if (others) {
	tell_from_inside(others, msgs[sizeof(who)], MSG_INDENT, who);
    }
}
// }}}
// varargs void simple_action(mixed msg, array obs...) {{{
//:FUNCTION simple_action
//Generate and send messages for an action involving the user and possibly
//some objects
varargs void simple_action(mixed msg, array obs...) {
    string us;
    string others;
    object env;
    object *who;
    object to = this_object();

    if( !sizeof( msg )) return;
    /* faster to only make who once */
    who = ({ to });
    if (pointerp(msg))
	msg = msg[random(sizeof(msg))];

    us = compose_message(to, msg, who, obs...);
    others = compose_message(0, msg, who, obs...);

    env = environment(to);
    if(env) {
        tell(to, us, MSG_INDENT); 
        tell_environment(to, others, MSG_INDENT, who); 
    }
}
// }}}
// varargs void my_action(mixed msg, array obs...) {{{
//:FUNCTION my_action
//Generate and send a message that should only be seen by the person doing it
varargs void my_action(mixed msg, array obs...) {
    string us;
    object *who;
    object to = this_object();

    if (!sizeof( msg )) return;
    who = ({ to });
    if (pointerp(msg))
	msg = msg[random(sizeof(msg))];
    us = compose_message(to, msg, who, obs...);
    tell(to, us, MSG_INDENT);
}
// }}}
// varargs void other_action(mixed msg, array obs...) {{{
//:FUNCTION other_action
//Generate and send a message that should only be seen by others
varargs void other_action(mixed msg, array obs...) {
    string others;
    object *who;
    object to = this_object();

    if( !sizeof(msg)) return;
    who = ({ to });
    if (pointerp(msg))
	msg = msg[random(sizeof(msg))];
    others = compose_message(0, msg, who, obs...);
    tell_environment(to, others, MSG_INDENT, who);
}
// }}}
// varargs void targetted_action(mixed msg, object target, array obs...) {{{
//:FUNCTION targetted_action
//Generate and send a message involving the doer and a target (and possibly
//other objects)
varargs void targetted_action(mixed msg, object target, array obs...) {
    string us, them, others;
    object *who;
    object to = this_object();

    if( !sizeof(msg)) return;
    who = ({ to, target });
    if (pointerp(msg))
	msg = msg[random(sizeof(msg))];
    us = compose_message(to, msg, who, obs...);
    them = compose_message(target, msg, who, obs...);
    others = compose_message(0, msg, who, obs...);
    tell(to, us, MSG_INDENT);
    if(!target->query_unconscious() && to != target) 
        tell(target, them, MSG_INDENT);
    tell_environment(to, others, MSG_INDENT, who);
}
// }}}
