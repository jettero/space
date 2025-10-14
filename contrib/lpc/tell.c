//:COMMAND
// The tell command is used for private communication.
// only the target of this command can actually hear what you tell them.
// It also doesn't matter if they're in the room; though, that's likely
// to change in the future.
// 
// Example:
// tell dorn Hi, I found a bug!  Do you have time to look at it? :(
// 
// Also see:  reply
// 
// $Id: tell.c,v 1.8 2008/03/09 15:19:44 bakhara Exp $

#include <mudlib.h>
#include <commands.h>

inherit CMD;
inherit M_GRAMMAR;
inherit M_COMPLETE;
inherit M_ANSI;

void create()
{
    ::create();
    no_redirection();
}

private void main(string arg)
{
    string lcuser;
    object tb = this_body();
    string user;
    // string host;
    mixed tmp;
    // string array words;
    // string muds;
    // string array previous_matches;
    // string array matches;
    // int i, j;
    string mystring;
    string deststring;
    object who;

    if(!arg) {
        out("Usage: tell <user> <message>\n");
        return;
    }

    /* imud {{{
    if(sscanf(arg,"%s@%s", user, tmp) == 2) {
        muds = IMUD_D->query_up_muds();
        words = explode(tmp, " ");
        j = sizeof(words);
        tmp = "";

        for(i=0;i<j;i++) {
            tmp += " " + words[i];
            if(tmp[0] == ' ')
            tmp = tmp[1..];
            matches = find_best_match_or_complete(tmp, muds);
            if(!sizeof(matches))
            {
            break;
            }
            previous_matches = matches;
        }

        if(previous_matches) {
            if(sizeof(previous_matches) > 1) {
                out("Vague mud name.  could be: " + implode(previous_matches, ", ") + "\n");
                return;
            }                

            host = previous_matches[0];
            arg  = implode(words[i..], " ");
            if(host == mud_name()) {
                main(user+" "+arg);
                return;
            }

            if( arg[0] == ';' || arg[0] == ':' ) {
                array soul_ret;
                
                arg = arg[1..];

                // Heuristic: check for a use of a targetted emote with no
                // arguments, and do the Right Thing.
                if ((tmp = SOUL_D->query_emote(arg)) && tmp["LIV"])
                    arg += " " + user + "@" + host;

                soul_ret = SOUL_D->parse_imud_soul(arg);
                if(!soul_ret)  {
                    IMUD_D->do_emoteto(host, user, arg);
                    tb->my_action(sprintf("You emote to %s@%s: %s %s\n", capitalize(user), host, tb->query_name(), arg));
                    return;
                }

                IMUD_D->do_emoteto(host,user,soul_ret[1][<1]);
                tb->my_action(sprintf("*%s", soul_ret[1][0]));
                return;
            }

            IMUD_D->do_tell(host, user, arg);
            tb->my_action(sprintf("You tell %s@%s: %s\n", capitalize(user), host, arg));
            return;
        }
    }
    }}} */

    if(sscanf(arg, "%s %s", user, arg) != 2) {
        out("Usage: tell <user> <message>\n");
        return;
    }

    who = find_body(lcuser = lower_case(user));

    if(!who) {
        outf("Couldn't find %s.\n", user);
        return;
    }

    if (who->query_invis() && !adminp(this_user()) ) {
        outf("Couldn't find %s.\n", user);
        return;
    }

    if (!who->query_link() || !interactive(who->query_link())) {
        outf("%s is linkdead.\n", who->query_name());
        return;
    }

    tb->set_mapvar("rtell", lcuser);

    if( arg[0] == ':' || arg[0] == ';' ) {
        array soul_ret;
        int tindex;

        arg = arg[1..];
        // Heuristic: check for a use of a targetted emote with no
        // arguments, and do the Right Thing.
        if ((tmp = SOUL_D->query_emote(arg)) && tmp["LIV"])
            arg += " " + user;

        soul_ret = SOUL_D->parse_soul(arg);

        if(!soul_ret)  {
            mystring = sprintf("You emote to %s: %s %s\n", who == tb ? "yourself" : who->query_name(), tb->query_name(),arg);
            deststring = sprintf("*%s %s\n", tb->query_name(), arg);

        } else {
            mystring = sprintf("(tell)%%^RESET%%^ %s", soul_ret[1][0]);

            if((tindex = member_array(who, soul_ret[0])) == -1)  {
                deststring = sprintf("(tell)%%^RESET%%^ %s", soul_ret[1][<1]);

            } else {
                deststring = sprintf("(tell)%%^RESET%%^ %s", soul_ret[1][tindex]);
            }
        }

    } else {
        string color = tb->get_mapvar("chan_color__tell"); if( !color ) color = "%^SAY%^";
        mystring   = color + sprintf("You tell %s%%^RESET%%^, \"%s\"\n", who == tb ? "yourself" : who->query_name(), punctuate(arg));

        color = who->get_mapvar("chan_color__tell"); if( !color ) color = "%^SAY%^";
        deststring = color + capitalize(tb->query_name()) + " tells you%^RESET%^, \"" + punctuate(arg) + "\"\n";
    }

    tb->my_action(mystring);

    if(who != tb) {
        who->receive_private_msg(deststring, MSG_INDENT);
        who->set_reply(this_user()->query_userid());
    }
}

nomask int valid_resend(string ob) {
    return ob == "/cmds/player/reply";
}
