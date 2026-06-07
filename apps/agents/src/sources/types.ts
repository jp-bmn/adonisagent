/**
 * Every source-specific scraper returns this shape.
 * The scoring + persistence layer doesn't care which source it came from.
 */

export interface RawItem {
  /** Where it came from: 'beckers' | 'serper' | 'hospital_newsroom' | etc. */
  sourceType: string;
  /** Public URL to the original content - required */
  url: string;
  /** Headline / title text */
  title: string;
  /** Body or summary text — what the LLM and scorer read */
  text: string;
  /** ISO timestamp if publication date is known */
  publishedAt?: string;
}
