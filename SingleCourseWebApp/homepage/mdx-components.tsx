import type { MDXComponents } from 'mdx/types'

// Define the frontmatter type
type Frontmatter = {
  title?: string
  publishedAt?: string
  summary?: string
  tags?: string
}

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    ...components,
    // Add wrapper for frontmatter content
    wrapper: ({ children }: { children: React.ReactNode }) => {
      return <article className="mdx-content">{children}</article>
    },
    // Keep existing Cover component
    Cover: ({
      src,
      alt,
      caption,
    }: {
      src: string
      alt: string
      caption: string
    }) => {
      return (
        <figure>
          <img src={src} alt={alt} className="rounded-xl" />
          <figcaption className="text-center">{caption}</figcaption>
        </figure>
      )
    },
    // Add h1 component to handle title styling consistently
    h1: ({ children }) => (
      <h1 className="mb-8 text-2xl font-bold tracking-tight">{children}</h1>
    ),
  }
}
