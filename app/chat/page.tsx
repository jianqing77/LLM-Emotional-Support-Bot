'use client';

import Image from 'next/image';
import Link from 'next/link';
import logoIconImg from '@/public/logo-icon.svg';
import { useState, useEffect } from 'react';
import { PlaceholdersAndVanishInput } from '@/components/ui/placeholders-and-vanish-input';

interface Message {
    id: number;
    text: string;
    sender: 'user' | 'bot';
}

export default function Chat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [hasSentMessage, setHasSentMessage] = useState(false);

    const placeholders = [
        "Can you help me understand why I've been so sad?",
        'Lately, I feel anxious all the time. Why is that?',
        'I have been feeling very tired and unmotivated. Is this normal?',
        "How can I tell if I'm dealing with depression?",
        "I'm finding it hard to cope with the loss of my job. Can you help?",
    ];

    const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(e.target.value);
    };

    const handleSend = () => {
        const newMessage: Message = {
            id: messages.length,
            text: inputValue,
            sender: 'user',
        };
        setMessages([...messages, newMessage]);
        getBotResponse(inputValue);
        setInputValue(''); // clear the input after sending
        setHasSentMessage(true);
    };

    // const getBotResponse = async (userInput: string) => {
    //     try {
    //         const response = await fetch('/api/generate', {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/json',
    //             },
    //             body: JSON.stringify({ query: userInput }),
    //         });

    //         if (!response.ok) {
    //             throw new Error('Network response was not ok');
    //         }

    //         const data = await response.json();
    //         const botMessage: Message = {
    //             id: messages.length + 1,
    //             text: data.followup, // 'followup' is the key in the JSON response
    //             sender: 'bot',
    //         };

    //         setMessages((prevMessages) => [...prevMessages, botMessage]);
    //     } catch (error) {
    //         console.error('There was a problem with the fetch operation:', error);
    //     }
    // };

    const getBotResponse = async (userInput: string) => {
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: userInput }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            if (data.followup && data.followup.length) {
                // Process each follow-up question individually
                data.followup.forEach((question: string, index: number) => {
                    const botMessage: Message = {
                        id: messages.length + 1 + index, // Ensure unique ID
                        text: question,
                        sender: 'bot',
                    };

                    setTimeout(() => {
                        setMessages((prevMessages) => [...prevMessages, botMessage]);
                    }, 1000 * index); // Delay subsequent messages to simulate typing
                });
            } else {
                // Handle the case where there are no follow-up questions
                const botMessage: Message = {
                    id: messages.length + 1,
                    text: 'No follow-up questions available.',
                    sender: 'bot',
                };
                setMessages((prevMessages) => [...prevMessages, botMessage]);
            }
        } catch (error) {
            console.error('There was a problem with the fetch operation:', error);
        }
    };

    return (
        <div className="h-[40rem] flex flex-col justify-center items-center px-4">
            {!hasSentMessage && (
                <div className="w-1/2 flex flex-col items-center justify-center flex-grow mt-16 sm:ms-10 text-center">
                    <Image
                        src={logoIconImg}
                        alt="Logo"
                        className="w-10 h-auto md:w-20 mb-2"
                    />
                    <div className="mt-7">
                        Whether you're feeling joyful and want to share your happiness, or
                        you're struggling with sadness, anxiety, or stress,{' '}
                        <span className="text-green-500 font-semibold">
                            EmotionListener
                        </span>{' '}
                        is here to provide a safe, private space for you to express your
                        feelings and thoughts. Our AI is designed with empathy at its
                        core, ensuring that you feel heard and understood. Let's talk
                        about what's on your mind today.
                    </div>
                </div>
            )}
            <div className="w-1/2 flex-1 overflow-auto p-4">
                {/* Messages */}
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`mt-11 px-4 py-3 my-2 rounded-xl mb-7 ${
                            message.sender === 'user'
                                ? 'text-popup flex justify-end border border-gray-400 '
                                : 'bg-zinc-800 text-white'
                        }`}>
                        {message.text}
                    </div>
                ))}
            </div>
            <PlaceholdersAndVanishInput
                placeholders={placeholders}
                onChange={handleInput}
                onSubmit={handleSend}
            />
        </div>
    );
}
