
const Pagination = ({ 
  currentPage = 1, 
  totalPages = 1, 
  onPageChange, 
  itemsPerPage = 10, 
  totalItems = 0,
  className = "",
  showPageNumbers = true,
  maxPageNumbers = 5
}) => {
  if (totalPages <= 1) return null;

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      onPageChange(page);
    }
  };

  const getPageNumbers = () => {
    const pages = [];
    const halfMax = Math.floor(maxPageNumbers / 2);
    
    let startPage = Math.max(1, currentPage - halfMax);
    let endPage = Math.min(totalPages, startPage + maxPageNumbers - 1);
    
    if (endPage - startPage + 1 < maxPageNumbers) {
      startPage = Math.max(1, endPage - maxPageNumbers + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return pages;
  };

  const pageNumbers = getPageNumbers();
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  return (
    <div className={`flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0 ${className}`}>
      {/* Информация о записях */}
      <div className="text-sm text-text-secondary font-rajdhani">
        Показано {startItem}-{endItem} из {totalItems} записей
      </div>

      {/* Навигация */}
      <div className="flex items-center space-x-2">
        {/* Кнопка "Первая" */}
        {currentPage > 1 && (
          <button
            onClick={() => handlePageChange(1)}
            className="px-3 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white hover:bg-accent-primary hover:bg-opacity-20 transition-colors font-rajdhani"
            title="Первая страница"
          >
            ⟨⟨
          </button>
        )}

        {/* Кнопка "Предыдущая" */}
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-4 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white hover:bg-accent-primary hover:bg-opacity-20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-rajdhani"
        >
          ⟨ Назад
        </button>

        {/* Номера страниц */}
        {showPageNumbers && (
          <div className="flex items-center space-x-1">
            {pageNumbers.map((page) => (
              <button
                key={page}
                onClick={() => handlePageChange(page)}
                className={`px-3 py-2 rounded-lg font-rajdhani font-bold transition-colors ${
                  page === currentPage
                    ? 'bg-accent-primary text-white'
                    : 'bg-surface-card border border-accent-primary border-opacity-30 text-text-secondary hover:text-white hover:bg-accent-primary hover:bg-opacity-20'
                }`}
              >
                {page}
              </button>
            ))}
          </div>
        )}

        {/* Выпадающий список страниц (альтернатива для больших списков) */}
        {!showPageNumbers && totalPages > 1 && (
          <select
            value={currentPage}
            onChange={(e) => handlePageChange(parseInt(e.target.value))}
            className="px-3 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-white font-rajdhani focus:outline-none focus:border-accent-primary"
          >
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
              <option key={page} value={page}>
                Страница {page}
              </option>
            ))}
          </select>
        )}

        {/* Кнопка "Следующая" */}
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-4 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white hover:bg-accent-primary hover:bg-opacity-20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-rajdhani"
        >
          Вперед ⟩
        </button>

        {/* Кнопка "Последняя" */}
        {currentPage < totalPages && (
          <button
            onClick={() => handlePageChange(totalPages)}
            className="px-3 py-2 bg-surface-card border border-accent-primary border-opacity-30 rounded-lg text-text-secondary hover:text-white hover:bg-accent-primary hover:bg-opacity-20 transition-colors font-rajdhani"
            title="Последняя страница"
          >
            ⟩⟩
          </button>
        )}
      </div>
    </div>
  );
};

export default Pagination;