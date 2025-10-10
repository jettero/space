// vi: foldmethod=marker foldlevel=0 syntax=lpc
// $Id: m_quirks.c,v 1.1 2004/08/20 19:46:44 dorn Exp $
//

// Variable definitions
int     quirks_freq_rolls           = 6;
int     quirks_freq_sides           = 10;

mixed   quirk_array                 = ({ });

int     quirk_at;
int     quirk_count;

void force_me(string);
void respond(string);

// Function definitions
//  d) M_QUIRKS
//      1) set_quirk_freq()
//      2) add_quirk()
//      3) clear_quirks()
//      4) do_quirks()

// void renew_quirk_at() {{{
void renew_quirk_at() {
    quirk_at    = roll(quirks_freq_rolls,quirks_freq_sides);
    quirk_count = 0;
}
// }}}
// void set_quirks_frequency( rolls, die ) {{{
void set_quirks_frequency( int rolls, int sides) {
    if ( (rolls > 0) && (sides > 0) ) {
        quirks_freq_rolls = rolls;
        quirks_freq_sides = sides;
    }
    renew_quirk_at();
}
// }}}
// array query_quirks_frequency( ) {{{
array query_quirks_frequency( ) {
    return({ quirks_freq_rolls, quirks_freq_sides });
}
// }}}
// void add_quirk( quirk ) {{{
void add_quirk( mixed quirk ) {
    quirk_array += ({ quirk });
}
// }}}
// void clear_quirks( ) {{{
void clear_quirks() {
    quirk_array = ({ });
}
// }}}
// void use_disgusting_humanoid_quirks() {{{
void use_disgusting_humanoid_quirks() {
    // yes, these are subjective.  And half of them probably are a bad idea. but anyway.
    add_quirk("emote $vpick $p nose");
    add_quirk("fart");
    add_quirk("emote $vscratch $p behind");
    add_quirk("emote $vcough up a loogie");
}
// }}}
// void use_humanoid_quirks() {{{
void use_humanoid_quirks() {
    // yes, these are subjective.  And half of them probably are a bad idea. but anyway.
    add_quirk("emote $vshift $o weight to $o other foot");
    add_quirk("emote $vadjust $o clothing");
    add_quirk("cough");
}
// }}}
// int get_quirks_count() {{{
int get_quirks_count() {
    return sizeof(quirk_array);
}
// }}}
// void standard_quirks() {{{
void standard_quirks() {
    object  to  = this_object();
    object  env = environment( to );
    mixed   do_quirk;

    //force_me("say I have " +get_quirks_count()+ " quirks, and my quirk count is at " +quirk_count+ "/" +quirk_at+ ".");
    if (quirk_count++ < quirk_at) {
        return;
    } else if ( get_quirks_count() <= 0 ) {
        return;
    } else {
        renew_quirk_at();
    }
    if (!env) return;

    //force_me("say Selecting a quirk");
    do_quirk = choice(quirk_array);

    //force_me("say Performing a quirk");
    if (functionp(do_quirk)) {
        //force_me("say it's a function");
        evaluate(do_quirk);
    } else {
        //force_me("say it's not a function");
        respond(do_quirk);
    }
}
// }}}
