import { defineConfig } from "vitepress";
import { type DefaultTheme } from 'vitepress'
import {
  groupIconMdPlugin,
  groupIconVitePlugin,
} from 'vitepress-plugin-group-icons'

const base = '/nORM/'

export default defineConfig({
  base,
  title: "nORM",
  description: "nORM documentation and SQL feature references.",

  lastUpdated: true,
  cleanUrls: true,
  metaChunk: true,

  markdown: {
    codeTransformers: [
      // We use `[!!code` and `@@include` in demo to prevent transformation,
      // here we revert it back.
      {
        postprocess(code) {
          return code
            .replaceAll('[!!code', '[!code')
            .replaceAll('@@include', '@include')
        }
      }
    ],
    config(md) {
      md.use(groupIconMdPlugin)
    },
  },

  vite: {
    plugins: [
      groupIconVitePlugin()
    ]
  },

  head: [
    ['link', { rel: 'icon', href: `${base}favicon.ico`, sizes: 'any' }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '32x32', href: `${base}favicon-32x32.png` }],
    ['link', { rel: 'icon', type: 'image/png', sizes: '16x16', href: `${base}favicon-16x16.png` }],
    ['link', { rel: 'apple-touch-icon', sizes: '180x180', href: `${base}apple-touch-icon.png` }],
    ['link', { rel: 'manifest', href: `${base}site.webmanifest` }],
    ['meta', { name: 'theme-color', content: '#CE9354' }],
  ],

  themeConfig: {
    logo: { src: '/logo-24x24.svg', width: 24, height: 24 },
    nav: nav(),

    socialLinks: [
      { icon: 'github', link: 'https://github.com/devfros/norm' }
    ],

    search: {
      provider: "local",
    },

    sidebar: [
      {
        text: 'Overview',
        collapsed: false,
        items: [
          { text: 'What is nORM?', link: '/overview/what-is-norm' },
          { text: 'Installing nORM', link: '/overview/installing' },
        ]
      },
      {
        text: 'Tutorials',
        collapsed: false,
        items: [
          { text: 'Getting started with Python', link: '/tutorials/python' },
          {
            text: 'Other languages (in progress)',
            collapsed: true,
            items: [
              { text: 'Rust', link: '/tutorials/rust' },
              { text: 'Go', link: '/tutorials/golang' },
              { text: 'TypeScript', link: '/tutorials/typescript' },
            ],
          },
        ]
      },
      {
        text: 'Commands',
        collapsed: false,
        items: [
          { text: 'init', link: '/commands/init' },
          { text: 'targets', link: '/commands/targets' },
          { text: 'generate', link: '/commands/generate' },
          { text: 'check', link: '/commands/check' },
          { text: 'schema', link: '/commands/schema' },
          { text: 'migrations', link: '/commands/migrations' },
        ]
      },
      {
        text: 'Guides',
        collapsed: false,
        items: [
          { text: 'Fetching records', link: '/guides/select' },
          { text: 'Inserting records', link: '/guides/insert' },
          { text: 'Updating records', link: '/guides/update' },
          { text: 'Deleting records', link: '/guides/delete' },
          { text: 'Dynamic filtering', link: '/guides/dynamic_filtering' },
          { text: 'Dynamic sorting', link: '/guides/dynamic_sorting' },
          { text: 'Partial update', link: '/guides/partial_update' },
          { text: 'Embedding models', link: '/guides/embedding_models' },
          { text: 'Query comments', link: '/guides/query_comments' },
          { text: 'Schema comments', link: '/guides/schema_comments' },
        ]
      },
      {
        text: 'Reference',
        collapsed: false,
        items: [
          { text: 'CLI', link: '/reference/cli' },
          { text: 'Query annotations', link: '/reference/annotations' },
          { text: 'Macros', link: '/reference/macros' },
          {
            text: 'Configuration',
            items: [
              { text: 'General', link: '/reference/configuration' },
              { text: 'Python', link: '/reference/configuration/python' },
              { text: 'Rust', link: '/reference/configuration/rust' },
              { text: 'Go', link: '/reference/configuration/go' },
              { text: 'TypeScript', link: '/reference/configuration/typescript' },
            ],
            collapsed: true
          },
          { text: 'Database and language support', link: '/reference/db_and_lang_support' },
        ]
      },
      {
        text: 'sqlc',
        collapsed: false,
        link: '/sqlc/'
      },
    ],

    editLink: {
      pattern: 'https://github.com/devfros/norm/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2026-present Afros Rajabov'
    }
  },
});

function nav(): DefaultTheme.NavItem[] {
  return [
    { text: 'Quickstart', link: '/tutorials/python' },
    { text: 'Guides', link: '/guides/select' },
    { text: 'Reference', link: '/reference/cli' },
    { text: 'Playground', link: 'https://norm-play.vercel.app/' },
    {
      text: 'More',
      items: [
        {
          text: 'Changelog',
          link: 'https://github.com/devfros/norm/blob/main/CHANGELOG.md'
        },
        {
          text: 'Contributing',
          link: 'https://github.com/devfros/norm/blob/main/CONTRIBUTING.md'
        }
      ]
    }
  ]
}
