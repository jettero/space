// vi: foldmethod=marker foldlevel=0 syntax=lpc
// $Id: m_behavior.c,v 1.2 2004/08/20 19:57:18 dorn Exp $
//

//inherit m_wanders;
inherit M_WANDERS;
inherit M_QUIRKS;

// void have_standard_behavior() {{{
void have_standard_behavior() {
    object to = this_object();
    //object env = environment( to );

    if ( to->is_fighting() ) {
        // Do combat type stuff...
        // standard_morale();
        // standard_majik();
    } else {
        // Do non-combat type stuff...
        standard_wander();
        standard_quirks();
        // standard_be_aggressive(); // be be aggressive!
        // standard_band();
        // standard_majik();
    }
}
// }}}
