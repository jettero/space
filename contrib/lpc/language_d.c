#include <languages.h>

inherit M_GRAMMAR;
inherit M_MESSAGES;

int g_irc = 0;

mapping translation_mapping = ([ ]);

void set_irc()   { g_irc = 1; }
void set_noirc() { g_irc = 0; }

string slight_accent(int is_speaking, string s) {
    s = replace_string(s, "oing", "oyin'");
    s = replace_string(s, "ing",  "in'");
    s = replace_string(s, "the",  "da");
    s = replace_string(s, "wh",   "v");
    s = replace_string(s, "j",    "y");
    s = replace_string(s, "l",    "rh");

    s = replace_string(s, "Oing", "Oyin'");
    s = replace_string(s, "Ing",  "In'");
    s = replace_string(s, "The",  "Da");
    s = replace_string(s, "Wh",   "V");
    s = replace_string(s, "J",    "Y");
    s = replace_string(s, "L",    "Rh");

    s = replace_string(s, "OIng", "Oyin'");
    s = replace_string(s, "INg",  "In'");
    s = replace_string(s, "THe",  "Da");
    s = replace_string(s, "WH",   "V");

    s = replace_string(s, "OINg", "Oyin'");
    s = replace_string(s, "ING",  "IN'");
    s = replace_string(s, "THE",  "DA");

    s = replace_string(s, "OING", "OYIN'");

    return s;
}

string heavy_accent(int is_speaking, string s) {
    s = replace_string(s, "th", "t");
    s = replace_string(s, "sh", "s");
    s = replace_string(s, "ch", "k");
    s = replace_string(s, "c",  "k");
    s = replace_string(s, "y",  "i");
    s = replace_string(s, "j",  "i");

    s = replace_string(s, "Th", "T");
    s = replace_string(s, "Sh", "S");
    s = replace_string(s, "Ch", "K");
    s = replace_string(s, "C",  "K");
    s = replace_string(s, "Y",  "I");
    s = replace_string(s, "J",  "I");

    s = replace_string(s, "TH", "T");
    s = replace_string(s, "SH", "S");
    s = replace_string(s, "CH", "K");
    return slight_accent(is_speaking, s);
}

string babble_accent(int is_speaking, string s) {
    s = replace_string(s, "the ", "");
    s = replace_string(s, "and ", "");
    s = replace_string(s, "to ",  "");
    s = replace_string(s, "a",    "ae");
    s = replace_string(s, "e",    "i");
    s = replace_string(s, "o",    "oi");
    s = replace_string(s, "u",    "v");

    s = replace_string(s, "The ", "");
    s = replace_string(s, "And ", "");
    s = replace_string(s, "To ",  "");
    s = replace_string(s, "A",    "Ae");
    s = replace_string(s, "E",    "I");
    s = replace_string(s, "O",    "Oi");
    s = replace_string(s, "U",    "V");

    s = replace_string(s, "THe ", "");
    s = replace_string(s, "ANd ", "");
    s = replace_string(s, "TO ",  "");

    s = replace_string(s, "THE ", "");
    s = replace_string(s, "AND ", "");
    return heavy_accent(is_speaking, s);
}

string complete_babble(int is_speaking, string s) {
    array  a  = explode(s, " ");
    array ret = ({});
    string s2;
    while(sizeof(a)) {
        s2   = choice(a);
        a   -= ({ s2 });
        ret += ({ s2 });
    }
    return babble_accent(is_speaking, implode(ret, " "));
}

int understanding_level(object speaker, object listener) {
    int is_speaking     =  speaker->query_active_language();
    int speaking_skill  =  speaker->query_lang_skill_for(is_speaking);
    int listening_skill = listener->query_lang_skill_for(is_speaking);

     if(listening_skill > 0)
        listener->practice_with_langauge(is_speaking);

    // By definition in languages.h, the lower the value, the
    // worse the speaking/listening skill.
    return min( ({ speaking_skill, listening_skill }) );
}

int word_boundary(string s, string sub, int start) {
    int end = start + (sizeof(sub)-1);

    // if( sub == "dorn" ) debug("dorn", s[start..end], (s[start-1]), (s[end+1]) );

    if( start>0         && ((s[start-1]>='a' && s[start-1]<='z') || (s[start-1]>='A' && s[start-1]<='Z')) ) return 0;
    if( end<sizeof(s)-1 && ((s[  end+1]>='a' && s[  end+1]<='z') || (s[  end+1]>='A' && s[  end+1]<='Z')) ) return 0;

    return 1;
}

void say_main(string s, string s2, object speaker) {
    int    is_speaking  = speaker->query_active_language();
    object e            = environment(speaker);
    array  listeners    = filter(all_inventory(e), (: $1->is_living() :));
    int    l_level;
    string actual;
    string color;
    array listeners_at_lev;
    int pos;

    int irc = 0;
    if( g_irc || (ctime(time())[4..9]) == "Apr  1" )
        irc = 1;

    listeners -= ({ speaker });
    translation_mapping = ([ ]);

    speaker->practice_with_active_language();
    if( !irc ) {
        actual = compose_message(speaker, s + ", \"$o\"", ({ speaker }), s2[<3..<1] == "lol" ? s2 : punctuate(s2));

    } else {
        actual = compose_message(speaker, sprintf("%%^BOLD%%^%%^BLUE%%^<%%^RED%%^%s%%^BLUE%%^>%%^RESET%%^: ",
            speaker->query_primary_id()) + "$o", ({ speaker }), s2);
    }

    if( color = speaker->get_mapvar("chan_color__say") ) {
        tell(speaker, replace_string(actual, "%^SAY%^", color), MSG_INDENT, ({ speaker }));

    } else {
        tell(speaker, actual, MSG_INDENT, ({ speaker }));
    }

    foreach(object l in listeners) {
        // understanding level also practices with the language
        l_level = understanding_level(speaker, l);

        if(!arrayp(translation_mapping[l_level]))
                   translation_mapping[l_level]  = ({ l });
        else       translation_mapping[l_level] += ({ l });
    }

    foreach(int i in keys(translation_mapping)) {
        //actual = lower_case(s2);
        actual = s2;
        listeners_at_lev = translation_mapping[i];
        switch(i) {
            case L_BABBLE:   actual = complete_babble(is_speaking, actual);
            case L_NEWBIE:   actual =   babble_accent(is_speaking, actual);
            case L_NOT_GOOD: actual =    heavy_accent(is_speaking, actual);
            case L_NOT_BAD:  actual =   slight_accent(is_speaking, actual);
        }
        actual = (speaker->is_insane()) ? MADD_D->str_to_crazy(actual, speaker->query_insanity_level()) : actual;

        if( !irc ) {
            actual = compose_message(0, s + ", \"$o\"", ({ speaker }), s2[<3..<1] == "lol" ? s2 : punctuate(s2));

        } else {
            actual = compose_message(0, sprintf("%%^BOLD%%^%%^BLUE%%^<%%^RED%%^%s%%^BLUE%%^>%%^RESET%%^: ",
                 speaker->query_primary_id()) + "$o", ({ speaker }), actual);
        }

        foreach( object o in listeners_at_lev ) {
            string this_actual = actual;
            string hilite = 0;
            string hilite_tmp = 0;

            color = o->get_mapvar("chan_color__say");

            if( hilite_tmp = o->get_mapvar("chan_color__hilite") ) {
                foreach(string n in o->query_id()) {
                    if( (pos = strsrch(lower_case(actual), lower_case(n))) >= 0 ) {
                        if( word_boundary(actual, n, pos) ) {
                            hilite = hilite_tmp;
                            break;
                        }
                    }
                }
            }

            if( hilite ) {
                FAKECH_D->insert_line("hilite", o, this_actual);
                this_actual = replace_string(this_actual, "%^SAY%^", hilite);

            } else if( color ) {
                this_actual = replace_string(this_actual, "%^SAY%^", color);
            }

            tell(o, this_actual, MSG_INDENT, ({ speaker }));
        }
    }
}
