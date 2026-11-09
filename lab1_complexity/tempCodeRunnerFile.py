SEARCHES = {"Линейный поиск": linear_search, "Двоичный поиск": binary_search}
search_cases = lk.search_cases_table(SEARCHES)
lk.plot_search_overview(search_cases)
lk.plot_search_positions(search_cases)
