import pdfplumber


def get_chunks(pdf,chunk_size = 500, overlap = 50, separators = None):

    chunks = []

    with pdfplumber.open(pdf) as pdf:

        
        
        
        for page in pdf.pages:

            text = page.extract_text()
            if not text:
                continue

            page_chunk = recursive_chunk(text,chunk_size,overlap,separators)
            chunks.extend(page_chunk)
        
    return chunks


def recursive_chunk(text, chunk_size = 500, overlap = 50, separators = None):

    if separators is None:

        separators = ["\n\n", "\n", ". ", " ", ""]

    def _split(text, seps):


        if len(text) <= chunk_size or not seps:

            if text.strip():

                return [text.strip()]
            
            else:

                return []
        
        sep = seps[0]
        remaining_seps = seps[1:]
        chunks = []
        current_chunk = ""
        parts = text.split(sep)

        for part in parts:

            if current_chunk:

                proposed = current_chunk + sep + part
            
            else:

                proposed = part
            
            if len(proposed) <= chunk_size:

                current_chunk = proposed
            
            else:

                if current_chunk.strip():
                    
                    chunks.append(current_chunk.strip())
                
                if len(part) <= chunk_size:

                    if overlap:

                        overlap_text = current_chunk[-overlap:]
                    else:

                        overlap_text = ""
                    
                    current_chunk = overlap_text + part
                
                else:

                    sub_chunks = _split(part,remaining_seps)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
            
        if current_chunk.strip():

            chunks.append(current_chunk.strip())
        
        return chunks
    
    return _split(text,separators)