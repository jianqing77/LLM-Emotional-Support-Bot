/** @type {import('tailwindcss').Config} */
import flowbite from 'flowbite-react/tailwind';
import forms from '@tailwindcss/forms';

module.exports = {
    content: [
        './pages/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
        './app/**/*.{js,ts,jsx,tsx,mdx}',
        flowbite.content(),
    ],
    theme: {
        extend: {
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'gradient-conic':
                    'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
            },
            colors: {
                background: 'var(--background)',
                foreground: 'var(--foreground)',
                popup: 'var(--popup)',
                popupGreenLight: 'var(--popup-green-100)',
                popupGreenDark: 'var(--popup-green-200)',
            },
        },
    },
    plugins: [flowbite.plugin(), forms],
};
