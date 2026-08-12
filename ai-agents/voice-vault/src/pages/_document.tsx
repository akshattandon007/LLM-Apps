import { Html, Head, Main, NextScript } from "next/document";

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        {/* Theme init script — prevents FOUC */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('voicevault.theme') || 'light';
                  var dataTheme = theme === 'dark' ? 'warmdark' : 'warmlight';
                  document.documentElement.setAttribute('data-theme', dataTheme);
                } catch(e) {}
              })();
            `,
          }}
        />
      </Head>
      <body className="antialiased">
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}