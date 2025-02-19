'use client';

import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; // if you need support for GitHub Flavored Markdown
import Spinner from '@/components/spinner';
import Image from 'next/image';
import botImg from '@/./public/bot.jpg';
import userImg from '@/./public/user.jpg';
import Link from 'next/link';
import logoIconImg from '@/public/logo-icon.svg';
import { useState, useEffect } from 'react';
import { PlaceholdersAndVanishInput } from '@/components/ui/placeholders-and-vanish-input';
import { v4 as uuidv4 } from 'uuid';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
}

interface finalDiagnosisPayload {
    initialQuery: string;
    candidates: { [key: string]: string };
    followUpQuestions: string[];
    userFollowupResponse: string[];
}

export default function Chat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [initialQuery, setInitialQuery] = useState('');
    const [candidates, setCandidates] = useState({});

    const [inputValue, setInputValue] = useState('');
    const [hasSentMessage, setHasSentMessage] = useState(false);

    // state variables to track question
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [followUpQuestions, setFollowUpQuestions] = useState<string[]>([]);

    // set state for loading spinner
    const [loading, setLoading] = useState(false);

    // Array to store user responses for the follow up questions
    const [userFollowupResponse, setUserFollowupResponse] = useState<string[]>([]);

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

    /**
     * Handles the sending of user messages. It updates the messages state to include
     * the new user message, decides whether to call getBotResponse or processFollowupUserResponse
     * based on the message history, and resets the input field.
     */
    const handleSend = () => {
        const newMessage: Message = {
            id: uuidv4(), // UUID as ID
            text: inputValue,
            sender: 'user',
        };
        setMessages((prev) => [...prev, newMessage]);
        // Decide when to call getBotFollowupResponse
        if (messages.length === 0) {
            // If it's the first message, get the bot response for all the follow up questions
            getBotFollowupQuestions(inputValue);
        } else {
            // If it's not the first message, get the next follow up question
            processFollowupUserResponse(inputValue); // Handle subsequent messages
        }
        setInputValue(''); // clear the input after sending
        setHasSentMessage(true);
    };

    /**
     * Processes user inputs after the initial interaction. It sends a bot message based
     * on the current index of follow-up questions, updates the index, and stores user responses.
     * @param userInput - The text input from the user.
     */
    const processFollowupUserResponse = (userInput: string) => {
        if (currentQuestionIndex < followUpQuestions.length) {
            sendBotMessage(followUpQuestions[currentQuestionIndex]);
            setCurrentQuestionIndex((current) => current + 1);
        } else {
            const payload: finalDiagnosisPayload = {
                initialQuery: initialQuery,
                candidates: candidates,
                followUpQuestions: followUpQuestions,
                userFollowupResponse: userFollowupResponse,
            };
            getBotFinalDiagnosis(payload);
        }
        // Store user response about the follow up questions -- append to the list
        setUserFollowupResponse((prev) => [...prev, userInput]);
    };

    // Testing userFollowupResponse for the follow up questions
    useEffect(() => {
        console.log('Updated initial query:', initialQuery);
        console.log('Updated candidates:', candidates);
        console.log('Updated follow up questions:', followUpQuestions);
        console.log(
            'Updated user responses for follow-up questions:',
            userFollowupResponse
        );
    }, [candidates, initialQuery, followUpQuestions, userFollowupResponse]);

    /**
     * Sends a message from the bot by updating the messages state with a new bot message.
     * @param text - The message text to be sent by the bot.
     */
    const sendBotMessage = (text: string) => {
        const botMessage: Message = {
            id: uuidv4(), // use UUID as ID to ensure uniqueness
            text: text,
            sender: 'bot',
        };
        setMessages((prev) => [...prev, botMessage]);
    };

    /**
     * Fetches a bot response from a server API based on the user's input.
     * Handles network responses, updates follow-up questions, and sends initial follow-up messages if available.
     * @param userInput - The user's input text used to query the API.
     */
    const getBotFollowupQuestions = async (userInput: string) => {
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
            if (data.followupQuestions && data.followupQuestions.length) {
                setInitialQuery(data.initialQuery);
                setCandidates(data.candidates);
                setFollowUpQuestions(data.followupQuestions);
                setCurrentQuestionIndex(0);
                sendBotMessage(data.followupQuestions[0]); // Send the first follow-up question
                setCurrentQuestionIndex(1); // Prepare index for the next question
            } else {
                sendBotMessage('No follow-up questions available.');
            }
        } catch (error) {
            console.error('There was a problem with the fetch operation:', error);
        }
    };

    const getBotFinalDiagnosis = async (payload: finalDiagnosisPayload) => {
        setLoading(true);

        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            const result = data.result;
            sendBotMessage(result);
        } catch (error) {
            console.error('Error:', error);
            sendBotMessage('There was a problem processing your responses.');
        } finally {
            setLoading(false); // Hide spinner
        }
    };

    return (
        <div className="h-[38rem] flex flex-col justify-center items-center px-4">
            <div className="w-full flex justify-end pt-6 pe-6">
                <Link href="/">
                    <button
                        type="submit"
                        className="rounded-md bg-background px-4 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-gray-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
                        Exit
                    </button>
                </Link>
            </div>
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
                        <span className="text-green-500 font-semibold">MemeMinds</span> is
                        here to provide a safe, private space for you to express your
                        feelings and thoughts. Our AI is designed with empathy at its
                        core, ensuring that you feel heard and understood. Let's talk
                        about what's on your mind today.
                    </div>
                    <p className="text-center text-sm text-slate-400 mb-4 mt-5">
                        If you need professional advice, please consult a doctor.
                    </p>
                </div>
            )}
            <div className="flex-1 overflow-auto p-4 w-1/2 scrollbar-thumb-rounded-full scrollbar scrollbar-thumb-slate-700 scrollbar-track-slate-600">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex mt-11 my-2 rounded-xl mb-7 items-start ${
                            message.sender === 'user' ? 'justify-end' : 'justify-start'
                        } w-full`}>
                        {message.sender !== 'user' && (
                            <div className="w-10 h-10 rounded-full flex-shrink-0 mr-2 relative">
                                <Image
                                    src={botImg}
                                    alt="Bot Avatar"
                                    layout="fill"
                                    objectFit="cover"
                                    className="rounded-full"
                                />
                            </div>
                        )}
                        <div
                            className={`flex flex-col ${
                                message.sender === 'user' ? 'items-end' : 'items-start'
                            }`}>
                            <div
                                className={`${
                                    message.sender === 'user'
                                        ? 'text-popup border border-gray-500 rounded-xl px-4 py-3'
                                        : 'bg-zinc-800 text-white px-4 py-3 rounded-xl w-[95%]'
                                } inline-block`}>
                                <Markdown remarkPlugins={[remarkGfm]}>
                                    {message.text}
                                </Markdown>
                            </div>
                        </div>
                        {message.sender === 'user' && (
                            <div className="w-10 h-10 rounded-full flex-shrink-0 ml-2 relative">
                                <Image
                                    src={userImg}
                                    alt="User Avatar"
                                    layout="fill"
                                    objectFit="cover"
                                    className="rounded-full"
                                />
                            </div>
                        )}
                    </div>
                ))}
                {loading && <Spinner />}
            </div>

            <PlaceholdersAndVanishInput
                placeholders={placeholders}
                onChange={handleInput}
                onSubmit={handleSend}
            />
        </div>
    );
}
