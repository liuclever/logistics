import { useState } from 'react';
import { ArrowRightIcon } from 'tdesign-icons-react';
import { Button, Textarea } from 'tdesign-react';

interface ComposerProps {
  loading?: boolean;
  onSend: (message: string) => Promise<void> | void;
}

export function Composer({ loading, onSend }: ComposerProps) {
  const [value, setValue] = useState('');

  const handleSend = async () => {
    if (!value.trim() || loading) {
      return;
    }

    const current = value;
    setValue('');
    await onSend(current);
  };

  return (
    <div className="composer-shell">
      <Textarea
        value={value}
        autosize={{ minRows: 2, maxRows: 6 }}
        placeholder="输入物流指令，例如：创建从深圳到洛杉矶的新货运单"
        onChange={(nextValue) => setValue(nextValue)}
        onKeydown={(_, context) => {
          if (context.e.key === 'Enter' && !context.e.shiftKey) {
            context.e.preventDefault();
            void handleSend();
          }
        }}
      />
      <div className="composer-actions">
        <span>Enter 发送，Shift + Enter 换行</span>
        <Button
          className="composer-send-button"
          theme="default"
          loading={loading}
          onClick={() => void handleSend()}
        >
          <ArrowRightIcon size={16} />
          发送
        </Button>
      </div>
    </div>
  );
}
