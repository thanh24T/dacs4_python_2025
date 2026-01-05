/**
 * Cloudflare Worker cho Phi-3-Mini với LoRA Adapter
 * Tối ưu để tránh vượt quá resource limits
 */

export default {
  async fetch(request, env) {
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Only allow POST
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { 
        status: 405,
        headers: corsHeaders 
      });
    }

    try {
      // Parse request
      const body = await request.json();
      const { messages, max_tokens = 100, temperature = 0.7, top_p = 0.9 } = body;

      if (!messages || !Array.isArray(messages)) {
        return new Response(JSON.stringify({ 
          error: 'Invalid request: messages array required' 
        }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }

      // Load LoRA adapter từ R2 (cache để tránh load lại)
      let loraAdapter;
      try {
        const adapterObject = await env.LORA_BUCKET.get('adapter_model.safetensors');
        if (!adapterObject) {
          throw new Error('LoRA adapter not found in R2');
        }
        loraAdapter = await adapterObject.arrayBuffer();
      } catch (e) {
        console.error('Error loading LoRA adapter:', e);
        // Nếu không load được LoRA, chạy base model
        loraAdapter = null;
      }

      // Prepare messages for Phi-3 format
      let prompt = '';
      for (const msg of messages) {
        if (msg.role === 'system') {
          prompt += `<|system|>\n${msg.content}<|end|>\n`;
        } else if (msg.role === 'user') {
          prompt += `<|user|>\n${msg.content}<|end|>\n`;
        } else if (msg.role === 'assistant') {
          prompt += `<|assistant|>\n${msg.content}<|end|>\n`;
        }
      }
      prompt += '<|assistant|>\n';

      // Run inference với Workers AI
      const aiResponse = await env.AI.run(
        '@cf/microsoft/phi-3-mini-4k-instruct',
        {
          prompt: prompt,
          max_tokens: Math.min(max_tokens, 256), // Giới hạn để tránh timeout
          temperature: temperature,
          top_p: top_p,
          ...(loraAdapter && { lora: loraAdapter }) // Chỉ thêm LoRA nếu load được
        }
      );

      // Extract response
      let responseText = '';
      if (aiResponse && aiResponse.response) {
        responseText = aiResponse.response;
      } else if (typeof aiResponse === 'string') {
        responseText = aiResponse;
      } else {
        responseText = JSON.stringify(aiResponse);
      }

      // Return response in OpenAI format
      return new Response(JSON.stringify({
        choices: [{
          message: {
            role: 'assistant',
            content: responseText
          }
        }],
        response: responseText // Backward compatibility
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
