'use client';

import Image from 'next/image';
import logoIconImg from '@/public/logo-icon.svg';
import { useState, useEffect } from 'react';
import { PlaceholdersAndVanishInput } from '@/components/ui/placeholders-and-vanish-input';
import { v4 as uuidv4 } from 'uuid';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'bot';
}

export default function Chat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [hasSentMessage, setHasSentMessage] = useState(false);

    // state variables to track question
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [followUpQuestions, setFollowUpQuestions] = useState<string[]>([]);

    // Array to store user responses for the follow up questions
    const [userFollowupResponse, setUserFollowupResponse] = useState<string[]>([]);

    const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        setInputValue(e.target.value);
    };

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

    const processFollowupUserResponse = (userInput: string) => {
        if (currentQuestionIndex < followUpQuestions.length) {
            sendBotMessage(followUpQuestions[currentQuestionIndex]);
            setCurrentQuestionIndex((current) => current + 1);
        } else {
            // TODO: after the followUpQuestions were done, we should process to the next step
            sendBotMessage('Thank you for your responses.');
        }
        // Store user response about the follow up questions -- append to the list
        setUserFollowupResponse((prev) => [...prev, userInput]);
    };

    // Testing userFollowupResponse for the follow up questions
    useEffect(() => {
        console.log(
            'Updated user responses for follow-up questions:',
            userFollowupResponse
        );
    }, [userFollowupResponse]);

    const sendBotMessage = (text: string) => {
        const botMessage: Message = {
            id: uuidv4(), // use UUID as ID to ensure uniqueness
            text: text,
            sender: 'bot',
        };
        setMessages((prev) => [...prev, botMessage]);
    };

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
            if (data.followup && data.followup.length) {
                setFollowUpQuestions(data.followup);
                setCurrentQuestionIndex(0);
                sendBotMessage(data.followup[0]); // Send the first follow-up question
                setCurrentQuestionIndex(1); // Prepare index for the next question
            } else {
                sendBotMessage('No follow-up questions available.');
            }
        } catch (error) {
            console.error('There was a problem with the fetch operation:', error);
        }
    };

    return (
        <div className="h-[40rem] flex flex-col justify-center items-center px-4">
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
