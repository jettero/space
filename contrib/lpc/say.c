//:COMMAND
// The say command is pretty obvious, you've likely used it already.
// It lets you say things.  But wait!  It does much more!
// Try this:  say hi~~say hi:)~~say hi:P
// You might be pleasantly surprised.
//
// The following end punctuation do special things:
// !, ?, :), :(, ;), :0, :|, :P, =), =<, =>
// 
// A list of descriptions is available if you say nothing ("" not "nothing").
//
// $Id: say.c,v 1.62 2008/06/14 17:16:22 bakhara Exp $

#include <mudlib.h>
#include <daemons.h>

inherit CMD;
inherit M_GRAMMAR;

int  ivar;

array restrict = ({ 
    // "shandor",
    // "ripper",
    // "pfunk",
});

void create() {
    ::create();
    no_redirection();
}

void kick_souls(object tb) {
    object array a = tb->query_linkz() - ({ tb, 0 });

    debug("dorn", tb, a);

    a->soul_cage_swap();
}

void main(string s) {
    object tb = this_body();
    object tmp;

    if (!tb->query_awake()) {
        write("Wake up first.\n");
        return;
    }

    if( -1 != member_array(tb->query_primary_id(), restrict) ) {
        write("You have been restricted from using say.\n");
        return;
    }

    // if( tb->query_primary_id() == "pfunk" )
    //    s = upper_case(s);

    // if( tb->query_primary_id() == "pfunk" ) {
    //     array a = explode(s, " ");
    //     s = implode(a, " penis ");
    // }

    if ( tb->query_dead() ) {
        if(stringp(s)) {
            environment(tb)->receive_inside_msg(
                "%^SAY%^An eerie voice groans%^RESET%^, \""
                + s + ".\"\n"
            );
        }
        return;
    }

    if ( !s || s == "") {
        out(" !  exclaim\n");
        out(" ?  ask\n");
        out(" .  say.\n");
        out("... trail off ....\n");
        out("\\o/ arms in air\n");
        out(":!  chide\n");
        out(":)  happily declare\n");
        out(":/  smirk and say\n");
        out(":(  sadly mumble\n");
        out(";)  wink and suggest\n");
        out(":|  sullenly state\n");
        out(":0  look shocked and say\n");
        out(":p  stick out tongue and say\n");
        out("=<  sarcastically state\n");
        out("=>  facetiously say\n");
        out("x}  you so crazy\n");
        out("<<  warning ... um, use sparingly please\n");
        out("(complete text in parens)\n");

        return;
    }

    //  if( this_body()->query_primary_id() == "pfunk" )
    //      s = "braaaaaaaains...";

    //  if( this_body()->query_primary_id() == "ripper" )
    //      s = "braaaaaaaains...";

    //if( this_body()->query_primary_id() == "shandor" )
    // s = "blah, blah blah blah blah, blah blah. Blah! Blah blah blah... ";

    // s = replace_string(s, "really", "rly");
    // s = replace_string(s, "probably", "prolly");
    // s = replace_string(s, "prolly", "probably");
    s = replace_string(s, "comming",  "cyomyin'");
    s = replace_string(s, "commin",   "cyomyin'");
    s = replace_string(s, "011110010110010101110011", "yes");
    s = replace_string(s, "100111101010011011001110", "yes");

    s = replace_string(s, "yesb", "100111101010011011001110");
    s = replace_string(s, "yesB", "011110010110010101110011");

    s = replace_string(s, "preggo",  "(dude, I like cock)");
    s = replace_string(s, "prego",   "(dude, I like cock)");
    s = replace_string(s, "pre-go",  "(dude, I like cock)");
    s = replace_string(s, "preg-go", "(dude, I like cock)");
    s = replace_string(s, "pre-ggo", "(dude, I like cock)");
    s = replace_string(s, "pregg-o", "(dude, I like cock)");
    s = replace_string(s, "preg-o",  "(dude, I like cock)");
    s = replace_string(s, "pre-go",  "(dude, I like cock)");
    s = replace_string(s, "pregggo", "(dude, I like cock)");

    s = replace_string(s, "most", "moist");
    s = replace_string(s, "Most", "Moist");
    s = replace_string(s, "that's what she said", "moist");
    s = replace_string(s, "That's what she said", "Moist");

    s = replace_string(s, "I heart", "I &#9829;");

    // s = replace_string(s, " butt",   " [what what in the] butt");

    s = replace_string(s, "genious",    MADD_D->str_to_madness("genius"));
    s = replace_string(s, "wierd",      MADD_D->str_to_madness("weird"));
    s = replace_string(s, "dispite",    MADD_D->str_to_madness("despite"));
    s = replace_string(s, "definately", MADD_D->str_to_madness("definitely"));

    // s = "{the comments in this say are only my views, are not legally binding and cannot form an implied contract} " + s;

    // if( tb->query_name() == "Pfunk" )  {
    //     tb->simple_action("%^GREEN%^/* " + s + " -pfunk */");
    //     return;
    // }

    // if( tb->query_name() == "Shandor" )  {
    //     tb->simple_action("%^GREEN%^/* " + s + " -shandor */");
    //     return;
    // }

    if(tb->query_hidden()) {
        tb->force_me("unhide");
    }

    if( strsrch(lower_case(s), "get out!") >= 0 )
        call_out( (: kick_souls :), 1, tb );

    if( s[0 .. 2] == "-v " && (tmp = find_body(s[3..])) ) {
        tb->targetted_action("$N MODE #bakhara -v $t", tmp);
        restrict += ({ tmp->query_primary_id() });
        return;
    }

    if( s[0 .. 2] == "+v " && (tmp = find_body(s[3..])) ) {
        tb->targetted_action("$N MODE #bakhara +v $t", tmp);
        restrict -= ({ tmp->query_primary_id() });
        return;
    }

    ivar = strlen(s);  
    if(ivar == 1)   {
        // tb->simple_action("%^SAY%^$N $vsay%^RESET%^, \"$o\"", punctuate(s));
        LANG_D->say_main("%^SAY%^$N $vsay%^RESET%^", punctuate(s), this_body());
        return;
    }

    if( s[ivar-1] == '!' && s[ivar-2] == ':') 
      LANG_D->say_main("%^SAY%^$N $vchide%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( sizeof(s)>6 && s[0..5] == "......") {
        if( s[6] == ' ' ) {
            LANG_D->say_main("%^SAY%^... quite some time later, $n $vsay%^RESET%^", s[7..], this_body()); 

        } else {
            LANG_D->say_main("%^SAY%^... quite some time later, $n $vsay%^RESET%^", s[6..], this_body()); 
        }
    }

    else if( s[ivar-1] == '!' )
      LANG_D->say_main("%^SAY%^$N $vexclaim%^RESET%^", s, this_body());

    else if( s[ivar-1] == '?' )
      LANG_D->say_main("%^SAY%^$N $vask%^RESET%^", s, this_body());

    else if( s[ivar-1] == ')' && s[ivar-2] == '=') 
      LANG_D->say_main("%^SAY%^$N $vsmile brightly and $vsay%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == ')' && s[ivar-2] == ':') 
      LANG_D->say_main("%^SAY%^$N happily $vdeclare%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == '(' && s[ivar-2] == ':') 
      LANG_D->say_main("%^SAY%^$N sadly $vmumble%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == ')' && s[ivar-2] == ';') 
      LANG_D->say_main("%^SAY%^$N $vwink and $vsuggest%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == '0' && s[ivar-2] == ':') 
      LANG_D->say_main("%^SAY%^$N $vlook shocked and $vsay%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == '|' && s[ivar-2] == ':') 
      LANG_D->say_main("%^SAY%^$N sullenly $vstate%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == '<' && s[ivar-2] == '<' && s[ivar-3] == ' ') 
      LANG_D->say_main("%^SAY%^$N $vsay%^RESET%^", 
          ">>>>> " + upper_case(s[0..ivar-4]) + " <<<<<", this_body()); 

    else if( s[ivar-1] == '<' && s[ivar-2] == '<') 
      LANG_D->say_main("%^SAY%^$N $vsay%^RESET%^", 
          ">>>>> " + upper_case(s[0..ivar-3]) + " <<<<<", this_body()); 

    else if( (s[ivar-1] == 'd' || s[ivar-1] == 'D') && s[ivar-2] == ':') 
      LANG_D->say_main("%^SAY%^$N $vform a huge smile and $vsay%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( (s[ivar-1] == 'p' || s[ivar-1] == 'P') && s[ivar-2] == ':') 
      LANG_D->say_main("%^SAY%^$N $vstick out $p tongue and $vsay%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == '>' && s[ivar-2] == '=') 
      LANG_D->say_main("%^SAY%^$N facetiously $vsay%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == '<' && s[ivar-2] == '=') 
      LANG_D->say_main("%^SAY%^$N sarcastically $vstate%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == '}' && s[ivar-2] == 'x' && sizeof(s) < 200 )
      LANG_D->say_main("%^SAY%^$N $vsay%^RESET%^", 
          MADD_D->str_to_madness(s[0..ivar-3]), this_body()); 

    else if( s[ivar-1] == '/' && s[ivar-2] == ':') 
      LANG_D->say_main("%^SAY%^$N $vsmirk and $vsay%^RESET%^", 
          s[0..ivar-3], this_body()); 

    else if( s[ivar-1] == ')' && s[0] == '(' ) 
      LANG_D->say_main("%^SAY%^$N $vinterject parenthetically%^RESET%^", 
          s[1..ivar-2], this_body()); 

    else if( sizeof(s)>=3 && s[ivar-3] == '\\' && s[ivar-2] == 'o' && s[ivar-1] == '/' ) 
      LANG_D->say_main("%^SAY%^$N $vthrow $p hands in the air and $vshout%^RESET%^", 
          s, this_body()); 

    else if( sizeof(s)>=3 && s[ivar-1] == '.' && s[ivar-2] == '.' && s[ivar-3] == '.') 
      LANG_D->say_main("%^SAY%^$N $vtrail off saying%^RESET%^", s, this_body()); 

    else
      LANG_D->say_main("%^SAY%^$N $vsay%^RESET%^", s, this_body());
}

nomask int valid_resend(string ob) {
    return ob == "/cmds/player/converse";
}
