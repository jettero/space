//:COMMAND
// You can use this to assemble your own little fellings.
// If you 'emote hi man', everyone in the room will see:
// Newbie hi man.
// If you typed 'emote is cool as all get out':
// Newbie is cool as all get out.
//
// $Id: emote.c,v 1.3 2003/08/29 16:12:06 dorn Exp $

#include <mudlib.h>

inherit CMD;
inherit M_GRAMMAR;

void create() {
    ::create();
    no_redirection();
}

private void main(string message) {
    object tb = this_body();

    if(!tb->query_awake()) {
        write("Wake up first.\n");
        return;
    }

    if(!sizeof( message)) {
        write("Emote what?\n");
        return;
    }

    if ( message == ":)" ) {
        tb->simple_action("$N $vsmile gleefully.");
        return;
    }

    if ( message == ":(" ) {
        tb->simple_action("$N $vsigh sadly.");
        return;
    }

    if ( message == ":P" || message == ":p") {
        tb->simple_action("$N $vstick out $p tounge menacingly.");
        return;
    }

    if ( message == ":O" || message == ":o") {
        tb->simple_action("$N $vgasp.");
        return;
    }

    if ( message == ";)" ) {
        tb->simple_action("$N $vwink.");
        return;
    }

    if ( message == "w" ) {
        tb->simple_action("$N $vremind everyone to save.");
        tb->force_me("save");
        return;
    }

    if ( message == "q" ) {
        tb->simple_action("$N must go.  $N $vwave goodbye.");
        tb->force_me("quit");
        return;
    }

    if ( message == "wq" ) {
        tb->simple_action("$N $vremind everyone to save.");
        tb->simple_action("$N must go.  $N $vwave goodbye.");
        tb->force_me("quit");
        return;
    }

    if ( message == "wq!" ) {
        tb->force_me("say I gotta get outta here!!!!");
        tb->simple_action("$N $vremind everyone to save.");
        tb->force_me("quit");
        return;
    }

    if ( message == "q!" ) {
        tb->force_me("say I gotta get outta here!!!!");
        tb->force_me("quit");
        return;
    }

    if ( message == "w!" ) {
        tb->force_me("say I gotta save!");
        tb->force_me("save");
        tb->force_me("whew");
        return;
    }

    if ( to_int(message) > 0 )
        message = "attempts to goto line " + message + ".";

    if( sizeof(message) == 1 )
        message = ":-" + message;

    tb->simple_action(capitalize(punctuate(tb->a_short()  + " " +  message)));
}
