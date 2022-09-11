

def get_find_args(domain):
    new_domain = domain.dict(exclude={'per_page', 'page'})

    return new_domain, {"skip": (domain.page-1) * domain.per_page, "limit": domain.per_page}