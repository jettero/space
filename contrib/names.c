// This is from an ancient version of the lima-mudos mudlib. I had to go
// digging through some tape archives from circa y2k to find this ymmv.  I'm
// not sure what kind of attribution I could ever put here to link back to
// where I found it. It probably had a copyright notice at the top at one point
// -- and I almost certainly wasn't supposed to remove it, but in any case, I
// don't have it.
//
// Let me know if this is a problem for you and I'll fix it or remove it.

#include <hooks.h>

/* grammar related stuff */
private static string array ids;
private static string array plurals; // this is used?  Weird...
private static string array adjs;

private string primary_id, plural_id;

/* calculated internally */
private static mixed internal_short;
/* unique objects are refered to as 'the' instead of 'a' */
private static int unique;
/* ... As are plural objects (eg: stairs) */
private static int plural;
private static int pair;
private static string pair_word = "pair";
/*
 * proper_name: Proper_name should only be set for objects who should not
 *     be refered to as "a xxx" or "the xxx"
 */
private static mixed proper_name;
private string inscription;

int show_this_many_adj_when_plural = 0;

/*
** Can be implemented by subclasses to provide additional stuff dynamically
*/
// string array fake_item_id_list();
string invis_name();
int test_flag(mixed);
int is_secret_to_tb();

varargs mixed call_hooks(string, mixed, mixed);
private void resync();

void set_inscription(string w) { inscription = w; parse_refresh(); }
string query_inscription() { return inscription; }

mixed direct_inscribe_obj_with_wrd(object o, string w) {
    if( owner(o) != this_body() )
        return "You don't have it.\n";

    return 1;
}

mixed direct_uninscribe_obj(object o) {
    if( owner(o) != this_body() )
        return "You don't have it.\n";

    if(!inscription)
        return "It's not inscribed with anything.\n";

    return 1;
}

void do_inscribe_obj_with_wrd(object o, string w) { set_inscription(w); }
void do_uninscribe_obj(object o)                  { set_inscription(0); }

void create() {
    parse_init();
    ids = ({});
    plurals = ({});
    adjs = ({});
    resync();
}

void set_this_many_adj_when_plural(int i) {
    show_this_many_adj_when_plural = i;
    resync();
}

string primary_adj(int is_plural_check) {
    if(!arrayp(adjs) || !sizeof(adjs))
        return "";

    if( is_plural_check && show_this_many_adj_when_plural ) {
        if( show_this_many_adj_when_plural > 0 )
            return implode(adjs[0..show_this_many_adj_when_plural-1], " ");
        else
            return implode(adjs[<(0-show_this_many_adj_when_plural)..], " ");
    }

    return implode(adjs, " ");
}

//:FUNCTION set_proper_name
//Set the proper name of an object.  Objects with proper names never have
//adjectives added in front of their names.
nomask void set_proper_name(string str) {
    proper_name = str;
    resync();
}

//:FUNCTION set_unique
//Unique objects are always refered to as 'the ...' and never 'a ...'
void set_unique(int x) {
    unique = x;
}

//:FUNCTION query_unique
//Return the value of 'unique'
int query_unique() {
    return unique;
}

//:FUNCTION set_plural
//Plural objects are referred to as "the", not "a"
void set_plural( int x ) {
    plural = x;
}

//:FUNCTION set_plural_id
//Plural objects are referred to as "the", not "a"
void set_plural_id( string id ) {
    plural_id = id;
    plurals -= ({ id });
    plurals += ({ id });
}

//:FUNCTION set_pair
varargs void set_pair( int x, string s ) {
    pair = x;
    pair_word = stringp(s) ? s : "pair";
}

//:FUNCTION query_plural
//Return the value of plural
int query_plural() {
    return plural;
}

//:FUNCTION calculate_extra
// returns a call_hooks to extra_short
// probably for extra descriptions from spells and things...
// -Dorn
string calculate_extra() {
    //:HOOK extra_short
    //The non-zero return values are added on to the end of the short 
    // descriptions when inv_list() is used (surrounded by parenthesis)
    return  
        call_hooks("extra_short", 
            function(string sofar, mixed this) {
                if (!this) return sofar;
                return sofar + " (" + this + ")";
            }, 
            ""
        );
}

private void resync() {
    if (!proper_name) {
        if (!primary_id && sizeof(ids))
            primary_id = ids[0];

        if (primary_id) {
            if(this_object()->is_just_a_mob()) {
                internal_short = "";
                foreach(string s in adjs) {
                    internal_short += s + " ";
                }
                internal_short += primary_id;

            } else {
                internal_short = primary_adj(0) + " " + primary_id;
            }

            while( internal_short[0] == ' ' )
                internal_short = internal_short[1..];

            if( internal_short[<4..] == "door" ) {
                foreach(string dir in ({"north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest", "up", "down"})) {
                    int i;

                    if( (i = strsrch(internal_short, dir + " door")) >= 0 ) {
                        internal_short = internal_short[0..i-1] + "(" + dir + ") door";
                        break;
                    }
                }
            }

        } else {
            internal_short = "nameless bauble";
        }

    } else {
        internal_short = proper_name;
    }

    parse_refresh();
}

//:FUNCTION short
//Return the 'short' description of a object, which is the name by which
//it should be refered to
varargs string short(int inv_req) {
    object to = this_object();
    object tb = this_body();
    object ow = owner(to);
    string tv = "";
    object env = root_environment(to);
    string p = pair ? pair_word + " of " : "";
    string attr = "";
    string tmp;

    if(!tb || !env || !inv_req || (ow && ow != tb) ) {
        if( inscription )
            return p + "{"+inscription+"} " + evaluate(internal_short);

        return p + evaluate(internal_short);
    }

    if( env->is_shop() && (tmp = to->query_shopkeep_value()) )
        tv = " " + tmp;

    if( tb && (environment(to)==tb || environment(tb)==env) ) {
        array a = ({ });

        if( to->is_majik() && tb->call_hooks("detect majik", HOOK_LOR, 0) )
            a += ({ " %^CYAN%^majik%^RESET%^" });

        if( to->is_good() && tb->call_hooks("detect good", HOOK_LOR, 0) )
            a += ({ " %^BOLD%^WHITE%^good%^RESET%^" });

        if( to->is_evil() && tb->call_hooks("detect evil", HOOK_LOR, 0) )
            a += ({ " %^BOLD%^WHITE%^evil%^RESET%^" });

        if( sizeof(a) )
            attr = "[" + implode(a, " ") + "]";
    }

    if( inscription )
        return p + "{"+inscription+"} " + evaluate(internal_short) + tv + attr;

    return p + evaluate(internal_short) + tv + attr;
}

//:FUNCTION plural_short
// returns the pluralized short()
// -Dorn
varargs string plural_short(array inv_req, int noun_only) {
    object to = this_object();
    object tb = this_body();
    object ow = owner(to);
    string tv;
    object env = root_environment(to);
    array ret = ({ });
    int i,j;

    string sh;
    string adj = "";

    if(noun_only != -724 && sizeof(adjs) )
        adj = primary_adj(1) + " ";

    if(pair) {
        sh = pluralize(pair_word) + " of " + adj + primary_id;
    } else if (plural) {
        sh = adj + primary_id;
    } else if (plural_id) {
        sh = adj + plural_id;
    } else {
        sh = adj + pluralize(primary_id);
    }

    if(!tb || !env || !arrayp(inv_req) || (ow && ow != tb) )
        return sh;

    if(env->is_shop()) {
        inv_req = map(inv_req, (: $1->query_shopkeep_value() :));

        j=0; 
        for(i=0; i<sizeof(inv_req); i++) {
            if(inv_req[j] != inv_req[i]) {
                if(inv_req[j]) {
                    ret += ({ "(" + ( (j+1==i) ? ""+(j+1): (j+1)+"-"+(i) ) 
                                          + ") " + inv_req[j][1..<2] });
                }
                j=i;
            }
        }
        if(j!=i) {
            if(inv_req[j]) {
                ret += ({ "(" + ( (j+1==i) ? ""+(j+1): (j+1)+"-"+(i) ) 
                                      + ") " + inv_req[j][1..<2] });
            }
        }
        tv = (sizeof(ret)) ? "[" + implode(ret, ", ") + "]" : 0;
    }

    if(!tv)
        return sh;

    return sh + " " + tv;
}

//:FUNCTION add_article
// returns a string with a or an added to the beginning of whatever string
// you give it.  Lame little dealy really...
// -Dorn
string add_article(string str) {
    if(this_object()->query_unique()) 
        return "the " + str;

    switch (str[0]) {
        case 'a':
        case 'e':
        case 'i':
        case 'o':
        case 'u':
            return "an " + str;
    }

    return "a " + str;
}

//:FUNCTION the_short
//return the short descriptions, with the word 'the' in front if appropriate
varargs string the_short(int inv_req) {
    if (!proper_name) 
        return "the " + short(inv_req);

    if( inscription )
        return evaluate(proper_name) + " {" + inscription + "}";

    return evaluate(proper_name);
}

//:FUNCTION a_short
//return the short descriptions, with the word 'a' in front if appropriate
varargs string a_short(int inv_req) {
    if (plural || unique) 
        return the_short(inv_req);

    if (!proper_name) 
        return add_article(short(inv_req));

    if( inscription )
        return evaluate(proper_name) + " {" + inscription + "}";

    return evaluate(proper_name);
}

/****** the id() functions ******/
int id(string arg) {
    if(!arrayp( ids)) return 0;
    return member_array(arg,ids) != -1;
}

int plural_id( mixed arg ) {
    if( !arrayp( plurals)) return 0;
    return member_array(arg, plurals) != -1;
}

// In the following, id handles _both_ id and plural, except in the _no_plural
// cases.
/****** add_ ******/

//:FUNCTION add_adj
//:Adds adjectives.  The first one _DOES NOT_ become the prim
//:primary adjective when using add_adj().
void
add_adj(string array adj... ) {
    if(!arrayp(adjs))
	adjs = adj;
    else
	adjs += adj;
    resync();
}

//:FUNCTION add_plural
//Add a plural id
void add_plural( string array plural... ) {
    if(!arrayp(plurals))
	plurals = plural;
    else 
	plurals += plural;
    resync();
}

//:FUNCTION add_id_no_plural
//Add an id without adding the corresponding plural
void add_id_no_plural( string array id... ) {
    // set new primary
    if(!arrayp(ids))
	ids = id;
    else
	ids += id;
    resync();
}

void del_id( string array id... ) {
    if(!arrayp(ids))
        error("Man, that's weird");
    else
        ids -= id;
    plurals -= map(id, (: pluralize :));
    resync();
}

//:FUNCTION fadd_id
//Add an id and it's corresponding plural
// but starting at the front...
// (ie, sets the primary id)
void fadd_id( string array id... ) {
    if(!arrayp(ids))
	ids = id;
    else
	ids = id + ids;

    plurals    = map(ids, (: pluralize :));
    primary_id = id[0];
    resync();
}

//:FUNCTION add_id
//Add an id and it's corresponding plural
void add_id( string array id... ) {
    if(!arrayp(ids))
	ids = id;
    else
	ids += id;

    plurals += map(id, (: pluralize :));
    resync();
}

/****** set_ ******/
void set_id( string array id... ) {
    if(!arrayp(id))
        error("you give me bad args... you silly person");
    ids = id;
    plurals = map(id, (: pluralize :));
    primary_id = id[0];
    resync();
}

void set_adj( string array adj... ) {
    if(!arrayp(adj))
        error("you give me bad args... you silly person");
    adjs = adj;
    resync();
}

/****** remove_ ******/
//:FUNCTION remove_id
//Remove the given id
// static  // fuck static -dorn
void remove_id( string array id... ) {
    if(!arrayp(ids))
	return;
    ids -= id;
    plurals -= map(id, (: pluralize :));
    resync();
}

void remove_adj( string array adj ... ) {
    if(!arrayp(ids))
	return;
    adjs -= adj;
    resync();
}

/****** clear_ ******/

//:FUNCTION clear_id
//removes all the ids of an object.
void clear_id() {
    ids = ({ });
    plurals = ({ });
    resync();
}

//:FUNCTION clear_adj
//Remove all the adjectives from an object
void clear_adj() {
    adjs = ({ });
    resync();
}

/****** query_ ******/

//:FUNCTION query_id
//Returns an array containing the ids of an object
string array query_id() {
    // string array fake = this_object()->fake_item_id_list();

    // if (fake) return fake + ids;
    return ids;
}

//:FUNCTION query_primary_id
//Returns the primary id of an object
string query_primary_id() {
    return primary_id;
}

//:FUNCTION query_primary_id
//Returns the primary name (primary adj + primary id) of an object
string query_primary_name() {
    return primary_adj(0) + primary_id;
}

//:FUNCTION query_adj
//return the adjectives
string array query_adj() {
    return adjs;
}

/****** parser interaction ******/

string array parse_command_id_list() {
    if (test_flag(INVIS))
        return ({ });

    if( this_object()->is_secret_to_tb() )
        return ({ });

    return ids;
}

nomask string array parse_command_plural_id_list() {
    if (test_flag(INVIS))
        return ({ });

    if( this_object()->is_secret_to_tb() )
        return ({ });

    return plurals;
}

nomask string array parse_command_adjectiv_id_list() {
    if (test_flag(INVIS))
        return ({ });

    if( this_object()->is_secret_to_tb() )
        return ({ });

    if( inscription )
        return adjs + ({ inscription });

    return adjs;
}
