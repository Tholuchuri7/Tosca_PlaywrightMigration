export class DateUtility {

  /**
   * Resolve a Tosca DATE expression.
   *
   * Syntax:
   * {DATE[baseDate][offsets][format]}
   *
   * Examples:
   * {DATE[][][dd/MM/yyyy]}
   * {DATE[][-50y][dd/MM/yyyy]}
   * {DATE[][+10d][]}
   * {DATE[{MONTHFIRST}][][dd/MM/yyyy]}
   * {DATE[01.02.2026][+1M][dd.MM.yyyy]}
   * {DATE[03/22/2027][+1M][MM/dd/yyyy]}
   */
  static resolve(
    expression: string,
    currentDate: Date = new Date()
  ): string {

    const match = expression.match(
      /^\{DATE\[(.*?)\]\[(.*?)\]\[(.*?)\]\}$/i
    );

    if (!match) {
      throw new Error(
        `Invalid Tosca DATE expression: ${expression}`
      );
    }

    const [
      ,
      baseExpression,
      offsetExpression,
      formatExpression
    ] = match;

    // --------------------------------------------------
    // 1. Resolve BASE DATE
    // --------------------------------------------------
    let date = this.resolveBaseDate(
      baseExpression,
      formatExpression,
      currentDate
    );

    // --------------------------------------------------
    // 2. Apply OFFSETS
    // Supports:
    // +10d
    // -10d
    // +1m
    // -2m
    // +1y
    // -50y
    // +1M+1d
    // -1y-2m+5d
    // --------------------------------------------------
    const offsets =
      offsetExpression.match(/[+-]\d+[dmy]/gi) ?? [];

    for (const offset of offsets) {

      const value = Number(
        offset.slice(0, -1)
      );

      const unit =
        offset.slice(-1).toLowerCase();

      switch (unit) {

        case "d":
          date.setDate(
            date.getDate() + value
          );
          break;

        case "m":
          date = this.addMonths(
            date,
            value
          );
          break;

        case "y":
          date = this.addYears(
            date,
            value
          );
          break;
      }
    }

    // --------------------------------------------------
    // 3. Apply FORMAT
    // --------------------------------------------------
    return this.format(
      date,
      formatExpression
    );
  }


  // ==================================================
  // BASE DATE
  // ==================================================

  private static resolveBaseDate(
    baseExpression: string,
    formatExpression: string,
    currentDate: Date
  ): Date {

    const base = baseExpression.trim();

    // --------------------------------------------------
    // Empty base date = TODAY
    // --------------------------------------------------
    if (!base) {
      return new Date(currentDate);
    }

    // --------------------------------------------------
    // {MONTHFIRST}
    // First day of current month
    // --------------------------------------------------
    if (
      base.toUpperCase() ===
      "{MONTHFIRST}"
    ) {
      return new Date(
        currentDate.getFullYear(),
        currentDate.getMonth(),
        1
      );
    }

    // --------------------------------------------------
    // Normalize Tosca quotes
    // --------------------------------------------------
    const normalizedBase =
      base.replace(/''/g, "");

    // --------------------------------------------------
    // Month name formats
    //
    // 01 Jan 2026
    // 01 January 2026
    // --------------------------------------------------
    const namedMonth =
      normalizedBase.match(
        /^(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})$/
      );

    if (namedMonth) {

      const day = Number(namedMonth[1]);
      const monthName =
        namedMonth[2].toLowerCase();
      const year = Number(namedMonth[3]);

      const monthMap: Record<string, number> = {

        jan: 0,
        january: 0,

        feb: 1,
        february: 1,

        mar: 2,
        march: 2,

        apr: 3,
        april: 3,

        may: 4,

        jun: 5,
        june: 5,

        jul: 6,
        july: 6,

        aug: 7,
        august: 7,

        sep: 8,
        sept: 8,
        september: 8,

        oct: 9,
        october: 9,

        nov: 10,
        november: 10,

        dec: 11,
        december: 11
      };

      if (
        monthMap[monthName] === undefined
      ) {
        throw new Error(
          `Unknown month name: ${monthName}`
        );
      }

      return this.createValidatedDate(
        year,
        monthMap[monthName],
        day,
        base
      );
    }

    // --------------------------------------------------
    // Determine numeric date format
    //
    // First try the explicit output format.
    // If output format is dd.MM.yyyy, then
    // 01.02.2026 is interpreted as 1 Feb 2026.
    //
    // This is important because:
    // 01.02.2026 by itself is ambiguous.
    // --------------------------------------------------
    const inferredFormat =
      this.detectNumericDateFormat(
        normalizedBase,
        formatExpression
      );

    if (inferredFormat) {

      const parts =
        normalizedBase.split(
          inferredFormat.separator
        );

      if (parts.length === 3) {

        let day: number;
        let month: number;
        let year: number;

        if (
          inferredFormat.order ===
          "DMY"
        ) {
          day = Number(parts[0]);
          month = Number(parts[1]);
          year = Number(parts[2]);
        }
        else {
          month = Number(parts[0]);
          day = Number(parts[1]);
          year = Number(parts[2]);
        }

        return this.createValidatedDate(
          year,
          month - 1,
          day,
          base
        );
      }
    }

    throw new Error(
      `Unsupported or ambiguous Tosca base date: ${base}`
    );
  }


  // ==================================================
  // DETECT NUMERIC DATE FORMAT
  // ==================================================

  private static detectNumericDateFormat(
    value: string,
    outputFormat: string
  ): {
    separator: string;
    order: "DMY" | "MDY";
  } | null {

    const separators = ["/", ".", "-"];

    const separator =
      separators.find(
        s => value.includes(s)
      );

    if (!separator) {
      return null;
    }

    const parts =
      value.split(separator);

    if (
      parts.length !== 3 ||
      parts.some(
        p => !/^\d+$/.test(p)
      )
    ) {
      return null;
    }

    const first = Number(parts[0]);
    const second = Number(parts[1]);
    const year = Number(parts[2]);

    if (
      year < 1000 ||
      year > 9999
    ) {
      return null;
    }

    // --------------------------------------------------
    // If output format gives us the order,
    // use it as the context.
    // --------------------------------------------------
    const cleanedFormat =
      outputFormat
        ?.replace(/''/g, "")
        .trim();

    if (cleanedFormat) {

      const normalizedFormat =
        cleanedFormat.toLowerCase();

      if (
        normalizedFormat.startsWith("dd")
      ) {
        return {
          separator,
          order: "DMY"
        };
      }

      if (
        normalizedFormat.startsWith("mm")
      ) {
        return {
          separator,
          order: "MDY"
        };
      }
    }

    // --------------------------------------------------
    // No explicit context.
    //
    // Use unambiguous ranges when possible.
    // --------------------------------------------------

    // 22/03/2027 -> definitely DMY
    if (first > 12 && second <= 12) {
      return {
        separator,
        order: "DMY"
      };
    }

    // 03/22/2027 -> definitely MDY
    if (second > 12 && first <= 12) {
      return {
        separator,
        order: "MDY"
      };
    }

    // --------------------------------------------------
    // Still ambiguous.
    //
    // Default to DMY because that is the default
    // convention used in this utility.
    // --------------------------------------------------
    return {
      separator,
      order: "DMY"
    };
  }


  // ==================================================
  // VALIDATE / CREATE DATE
  // ==================================================

  private static createValidatedDate(
    year: number,
    month: number,
    day: number,
    originalValue: string
  ): Date {

    const date =
      new Date(
        year,
        month,
        day
      );

    // JavaScript automatically rolls invalid dates.
    // Example:
    // 31 Feb → March
    //
    // Prevent that silently.
    if (
      date.getFullYear() !== year ||
      date.getMonth() !== month ||
      date.getDate() !== day
    ) {
      throw new Error(
        `Invalid Tosca base date: ${originalValue}`
      );
    }

    return date;
  }


  // ==================================================
  // SAFE MONTH ADDITION
  // ==================================================

  private static addMonths(
    date: Date,
    months: number
  ): Date {

    const result =
      new Date(date);

    const originalDay =
      result.getDate();

    // Set to 1 before changing month
    result.setDate(1);

    result.setMonth(
      result.getMonth() + months
    );

    // Last valid day in target month
    const lastDay =
      new Date(
        result.getFullYear(),
        result.getMonth() + 1,
        0
      ).getDate();

    result.setDate(
      Math.min(
        originalDay,
        lastDay
      )
    );

    return result;
  }


  // ==================================================
  // SAFE YEAR ADDITION
  // ==================================================

  private static addYears(
    date: Date,
    years: number
  ): Date {

    const result =
      new Date(date);

    const originalMonth =
      result.getMonth();

    const originalDay =
      result.getDate();

    // Prevent Feb 29 rollover
    result.setDate(1);

    result.setFullYear(
      result.getFullYear() + years
    );

    result.setMonth(
      originalMonth
    );

    const lastDay =
      new Date(
        result.getFullYear(),
        originalMonth + 1,
        0
      ).getDate();

    result.setDate(
      Math.min(
        originalDay,
        lastDay
      )
    );

    return result;
  }


  // ==================================================
  // FORMAT RESULT
  // ==================================================

  private static format(
    date: Date,
    format: string
  ): string {

    // Empty format = default
    if (
      !format ||
      !format.trim()
    ) {
      format = "dd/MM/yyyy";
    }

    // Tosca:
    // MM''/''dd''/''yyyy
    //
    // becomes:
    // MM/dd/yyyy
    format =
      format.replace(
        /''/g,
        ""
      );

    const dd =
      String(
        date.getDate()
      ).padStart(2, "0");

    const d =
      String(
        date.getDate()
      );

    const MM =
      String(
        date.getMonth() + 1
      ).padStart(2, "0");

    const M =
      String(
        date.getMonth() + 1
      );

    const yyyy =
      String(
        date.getFullYear()
      );

    const yy =
      yyyy.slice(-2);

    const shortMonths = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec"
    ];

    const longMonths = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December"
    ];

    const MMM =
      shortMonths[
        date.getMonth()
      ];

    const MMMM =
      longMonths[
        date.getMonth()
      ];

    return format.replace(
      /yyyy|MMMM|MMM|MM|dd|yy|M|d/g,
      token => {

        const values: Record<
          string,
          string
        > = {
          yyyy,
          MMMM,
          MMM,
          MM,
          dd,
          yy,
          M,
          d
        };

        return values[token];
      }
    );
  }
}