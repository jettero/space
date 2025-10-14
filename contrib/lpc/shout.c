//:COMMAND
// Shout Hi all!
// and everyone nearby will hear you.
//
// When the shout command is used everybody in the nearby rooms will hear your
// important news.  Use this command sparingly.  It's likely to get squashed
// eventually.  It can be very annoying.
//
// $Id: shout.c,v 1.2 2001/11/12 20:16:40 dorn Exp $

#include <mudlib.h>
inherit CMD;
inherit M_GRAMMAR;

void create() {
  ::create();
  no_redirection();
}

private void main(string s) {
    object env, tb, troom;
    string msg_s;
    if (!s || s == "") {
	out("Shout what?\n");
	return;
    }

    tb    = this_body();
    env   = environment( tb );
    msg_s = "%^BOLD%^%^CYAN%^" + tb->query_name() + " shouts%^RESET%^, \"" +
            punctuate(s) + "\"\n";
    env->receive_outside_msg(msg_s, MSG_INDENT);

    foreach(string d, string r in env->query_exits()) {
        troom = load_object(r);
        if(troom) {
            troom->receive_outside_msg(msg_s, MSG_INDENT);
        }
    }
}
