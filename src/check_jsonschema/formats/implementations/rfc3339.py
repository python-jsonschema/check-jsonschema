def validate(date_str: str) -> bool:
    """Validate a string as a RFC3339 date-time.

    This check does the fastest possible validation of the date string (in Python),
    deferring operations as much as possible to avoid unnecessary work.
    """
    try:
        # the following chars MUST be fixed values:
        #    YYYY-MM-DDTHH:MM:SSZ
        #        ^  ^  ^  ^  ^
        #
        # so start by checking them first
        # this keeps us as fast as possible in failure cases
        #
        # (note: "T" and "t" are both allowed under ISO8601)
        if (
            date_str[4] != "-"
            or date_str[7] != "-"
            or date_str[10] not in ("T", "t")
            or date_str[13] != ":"
            or date_str[16] != ":"
        ):
            return False

        # check for fractional seconds, which pushes the location of the offset/Z
        # record the discovered start postiion of the offset segment
        offset_start = 19
        if date_str[19] in (".", ","):
            offset_start = date_str.find("Z", 20)
            if offset_start == -1:
                offset_start = date_str.find("z", 20)
            if offset_start == -1:
                offset_start = date_str.find("+", 20)
            if offset_start == -1:
                offset_start = date_str.find("-", 20)
            # if we can't find an offset after `.` or `,` as a separator, it's wrong
            if offset_start == -1:
                return False

            # fractional seconds are checked to be numeric
            # the spec seems to allow for any number of digits (?) so there's no
            # length check here
            frac_seconds = date_str[20:offset_start]
            if not frac_seconds:
                return False
            if not frac_seconds.isnumeric():
                return False

        # now, handle Z vs offset
        # (note: "Z" and "z" are both allowed under ISO8601)
        z_offset = date_str[offset_start:] in ("Z", "z")
        if z_offset and len(date_str) != offset_start + 1:
            return False
        if not z_offset:
            if len(date_str) != offset_start + 6:
                return False
            if date_str[offset_start] not in ("+", "-"):
                return False
            if date_str[offset_start + 3] != ":":
                return False

        year = date_str[:4]
        if not year.isnumeric():
            return False
        year_val = int(year)

        month = date_str[5:7]
        if not month.isnumeric():
            return False
        month_val = int(month)
        if not 1 <= month_val <= 12:
            return False

        day = date_str[8:10]
        if not day.isnumeric():
            return False
        max_day = 31
        if month_val in (4, 6, 9, 11):
            max_day = 30
        elif month_val == 2:
            max_day = (
                29
                if year_val % 4 == 0 and (year_val % 100 != 0 or year_val % 400 == 0)
                else 28
            )
        if not 1 <= int(day) <= max_day:
            return False

        hour = date_str[11:13]
        if not hour.isnumeric():
            return False
        if not 0 <= int(hour) <= 23:
            return False
        minute = date_str[14:16]
        if not minute.isnumeric():
            return False
        if not 0 <= int(minute) <= 59:
            return False
        second = date_str[17:19]
        if not second.isnumeric():
            return False
        if not 0 <= int(second) <= 59:
            return False

        if not z_offset:
            offset_hour = date_str[offset_start + 1 : offset_start + 3]
            if not offset_hour.isnumeric():
                return False
            if not 0 <= int(offset_hour) <= 23:
                return False
            offset_minute = date_str[offset_start + 4 : offset_start + 6]
            if not offset_minute.isnumeric():
                return False
            if not 0 <= int(offset_minute) <= 59:
                return False
    except (IndexError, ValueError):
        return False
    return True
