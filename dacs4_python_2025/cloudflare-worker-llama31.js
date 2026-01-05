/**
 * Cloudflare Worker - Llama 3.1 8B Instruct
 * Model tốt nhất available trên Cloudflare Workers AI
 */

export default {
  async fetch(request, env) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { 
        status: 405, 
        headers: corsHeaders 
      });
    }

    try {
      const body = await request.json();
      const { messages, max_tokens = 100, temperature = 0.7 } = body;

      if (!messages || !Array.isArray(messages)) {
        return new Response(JSON.stringify({ 
          error: 'Invalid request: messages array required' 
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // Llama 3.1 8B Instruct - Model tốt nhất trên Cloudflare
      const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
        messages: messages,
        max_tokens: max_tokens,
        temperature: temperature
      });

      // Extract response
      let responseText = '';
      if (response && response.response) {
        responseText = response.response;
      } else if (typeof response === 'string') {
        responseText = response;
      } else {
        responseText = JSON.stringify(response);
      }

      // Return in OpenAI format
      return new Response(JSON.stringify({
        response: responseText,
        model: '@cf/meta/llama-3.1-8b-instruct',
        choices: [{
          message: {
            role: 'assistant',
            content: responseText
          }
        }]
      }), {
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        }
      });

    } catch (error) {
      console.error('Worker error:', error);
      
      return new Response(JSON.stringify({
        error: error.message || 'Internal server error',
        details: error.stack
      }), {
        status: 500,
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        }
      });
    }
  }
};
