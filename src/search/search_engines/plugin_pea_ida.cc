#include "pea_ida_search.h"
#include "search_common.h"

#include "../option_parser.h"
#include "../plugin.h"

using namespace std;

namespace plugin_pea_ida {
static shared_ptr<SearchEngine> _parse(OptionParser &parser) {
    parser.document_synopsis(
        "",
        "");
    parser.add_option<shared_ptr<Evaluator>>("eval", "evaluator for h-value");

    pea_ida_search::add_options_to_parser(parser);
    Options opts = parser.parse();

    shared_ptr<pea_ida_search::PeaIdaSearch> engine;
    if (!parser.dry_run()) {
        engine = make_shared<pea_ida_search::PeaIdaSearch>(opts);
    }

    return engine;
}

static Plugin<SearchEngine> _plugin("pea_ida", _parse);
}
