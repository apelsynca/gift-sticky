from enum import StrEnum

from sticky.exceptions import StickyRequestValidationError

type Sorting[PE] = tuple[PE, bool]


class _SortingGetter[PE: StrEnum]:
    def __init__(self, sort_property_enum: type[PE], default_sorting: list[str]) -> None:
        self.sort_property_enum = sort_property_enum
        self.default_sorting = default_sorting

    async def __call__(self, sorting: list[str] | None) -> list[Sorting[PE]]:
        if sorting is None:
            sorting = self.default_sorting

        parsed_sorting: list[tuple[PE, bool]] = []
        for criteria in sorting:
            desc = False
            if criteria[0] == "-":
                desc = True
                criteria = criteria[1:]
            try:
                parsed_sorting.append((self.sort_property_enum(criteria), desc))
            except ValueError:
                raise StickyRequestValidationError(
                    [
                        {
                            "loc": ("query", "sorting"),
                            "input": criteria,
                            "msg": "Invalid sorting criterion.",
                            "type": "enum",
                        }
                    ]
                )
        return parsed_sorting
