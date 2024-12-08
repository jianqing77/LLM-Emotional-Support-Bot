'use client';

import Image from 'next/image';
import logoImg from '@/public/logo.svg';
import logoIconImg from '@/public/logo-icon.svg';
import { TypewriterEffectSmooth } from '@/components/ui/typewriter-effect';

import Link from 'next/link';
import { PlaceholdersAndVanishInput } from '@/components/ui/placeholders-and-vanish-input';

const Home = () => {
    const words = [
        {
            text: 'Where',
        },
        {
            text: 'Your',
        },
        {
            text: 'Emotions',
            className: 'text-popupGreenLight',
        },
        {
            text: 'Meet',
        },
        {
            text: 'Understanding.',
            className: 'text-popup',
        },
    ];
    return (
        <div className="relative h-screen flex flex-col items-center justify-center text-white ">
            <div className="bubbles"></div>
            {/* Responsive positioned buttons for login and signup */}
            <div className="absolute top-0 right-0 mt-4 mr-4 md:mt-6 md:mr-6 flex space-x-2 md:space-x-4">
                <button className="border text-xs md:text-sm font-medium border-neutral-200 dark:border-white/[0.2]  dark:text-white px-2 md:px-4 py-1 md:py-2 rounded-full">
                    <span>Login</span>
                    <span className="absolute inset-x-0 w-1/2 mx-auto -bottom-px bg-gradient-to-r from-transparent  to-transparent h-px" />
                </button>
                <Link href="/signup">
                    <button className="border text-xs md:text-sm font-medium border-neutral-200 dark:border-white/[0.2]  dark:text-white px-2 md:px-4 py-1 md:py-2 rounded-full">
                        <span>Sign Up</span>
                        <span className="absolute inset-x-0 w-1/2 mx-auto -bottom-px bg-gradient-to-r from-transparent to-transparent h-px" />
                    </button>
                </Link>
            </div>
            {/* Centered content */}
            <div className="flex flex-col items-center justify-center flex-grow">
                <Image
                    src={logoIconImg}
                    alt="Logo"
                    className="w-10 h-auto md:w-20 mb-2"
                />
                <Image src={logoImg} alt="Logo" className="w-48 h-auto md:w-52 mb-2 " />
                {/* Typewriter Effect -- Slogan */}
                <div className="flex justify-center items-center w-full">
                    <TypewriterEffectSmooth words={words} />
                </div>
            </div>
            {/* Responsive button position */}
            <div className="w-full px-4 py-2 absolute bottom-24 md:bottom-44 left-0 flex items-center justify-center md:relative md:flex md:flex-col md:items-center md:justify-center h-20">
                <Link href="/signup">
                    <button className="button">
                        <span className="py-3 px-4 border rounded-full hover:bg-popupGreenDark hover:text-white hover:border-none">
                            GET STARTED
                        </span>
                    </button>
                </Link>
            </div>
        </div>
    );
};

export default Home;
