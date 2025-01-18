import React, { useState } from 'react';
import { Box, TextField, Button, Paper, Typography, CircularProgress } from '@mui/material';
import ReactMarkdown from 'react-markdown';

interface Message {
  type: 'user' | 'bot';
  content: string;
}

interface FinancialChatboxProps {
  ticker: string;  // Current ticker passed from parent component
}

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080'

const FinancialChatbox: React.FC<FinancialChatboxProps> = ({ ticker }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to chat
    const userMessage: Message = { type: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/api/${ticker}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: input }),
      });

      if (!response.ok) {
        throw new Error('Failed to get analysis');
      }

      const responseData = await response.json();
      
      // Add bot response to chat - now accessing nested data structure
      const botMessage: Message = { 
        type: 'bot', 
        content: responseData.data.data || responseData.data 
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      // Add error message to chat
      const errorMessage: Message = { 
        type: 'bot', 
        content: 'Sorry, I encountered an error analyzing the data.' 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setInput('');
    }
  };

  const MessageContent: React.FC<{ content: string, isUser: boolean }> = ({ content, isUser }) => {
    if (isUser) {
      return <Typography>{content}</Typography>;
    }
    
    return (
      <ReactMarkdown
        components={{
          h2: ({ children }) => (
            <Typography variant="h6" sx={{ fontWeight: 'bold', mt: 1, mb: 2 }}>
              {children}
            </Typography>
          ),
          p: ({ children }) => (
            <Typography sx={{ mb: 1.5 }}>{children}</Typography>
          ),
          strong: ({ children }) => (
            <Typography component="span" sx={{ fontWeight: 'bold' }}>
              {children}
            </Typography>
          ),
          ul: ({ children }) => (
            <Box component="ul" sx={{ pl: 2, mb: 1.5 }}>
              {children}
            </Box>
          ),
          li: ({ children }) => (
            <Typography component="li" sx={{ mb: 0.5 }}>
              {children}
            </Typography>
          ),
          table: ({ children }) => (
            <Box sx={{ overflowX: 'auto', mb: 2 }}>
              <table style={{ 
                borderCollapse: 'collapse', 
                width: '100%',
                fontSize: '0.875rem'
              }}>
                {children}
              </table>
            </Box>
          ),
          th: ({ children }) => (
            <th style={{ 
              border: '1px solid #ddd',
              padding: '8px',
              backgroundColor: '#f5f5f5',
              textAlign: 'left'
            }}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td style={{ 
              border: '1px solid #ddd',
              padding: '8px'
            }}>
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    );
  };

  return (
    <Paper elevation={3} sx={{ p: 2, maxWidth: 600, margin: 'auto', mt: 4 }}>
      <Box sx={{ 
        height: 400, 
        overflowY: 'auto', 
        mb: 2,
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          background: '#f1f1f1',
        },
        '&::-webkit-scrollbar-thumb': {
          background: '#888',
          borderRadius: '4px',
        },
        '&::-webkit-scrollbar-thumb:hover': {
          background: '#555',
        },
      }}>
        {messages.map((message, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
              mb: 2,
            }}
          >
            <Paper
              sx={{
                p: 2,
                maxWidth: message.type === 'user' ? '70%' : '85%',
                bgcolor: message.type === 'user' ? 'primary.light' : 'grey.50',
                color: message.type === 'user' ? 'white' : 'text.primary',
                borderRadius: 2,
                boxShadow: 2,
              }}
            >
              <MessageContent 
                content={message.content} 
                isUser={message.type === 'user'} 
              />
            </Paper>
          </Box>
        ))}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
      </Box>

      <form onSubmit={handleSubmit}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about financial analysis..."
            disabled={isLoading}
            size="small"
          />
          <Button 
            type="submit" 
            variant="contained" 
            disabled={isLoading || !input.trim()}
          >
            Send
          </Button>
        </Box>
      </form>
    </Paper>
  );
};

export default FinancialChatbox; 